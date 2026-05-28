#!/usr/bin/env python3
"""
命題: 縦に並ぶ複数行 (各行が左にアイコン + 右にテキスト) で、 テキスト左端 x が
揃っているか.

これは centering-judge skill の「参考実装」のひとつ。 そのまま呼んで使うための
固定ツールではない。 命題が違えば別スクリプトを書くこと。

主要仮定:
  - 行ごとの ROI (y_top, y_bot) を人手指定する
  - 各行が「左にアイコン + 1 つ以上のテキスト塊」の 2 ブロック以上を含む
  - 1 番目のブロック = アイコン、 2 番目以降 = テキスト塊として扱う

アルゴリズム:
  1. 背景マスク: RGB 最小値 < 230 を content とみなす
  2. 行 ROI ごとに各列の content profile (any) を作る
  3. 連続 True ブロックを抽出 (隣接 gap < gap_threshold なら統合)
  4. 各行で 2 番目以降のブロック左端 x = text_left を計測
  5. 全行で max(text_left) - min(text_left) を delta_max、 threshold 超過で FAIL

Usage:
    python3 multi_row_text_left_x_after_icon.py <image.png> \\
        --row row1 280 320 \\
        --row row2 340 380 \\
        --row row3 400 440 \\
        [--threshold 2.0] [--gap-threshold 3] [--debug-out <path>]

Exit codes:
    0: ALL_ALIGNED
    1: SOME_NOT_ALIGNED
    2: ERROR
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def find_blocks_in_row(
    is_content_row: np.ndarray,
    *,
    gap_threshold: int,
    min_block_width: int = 3,
) -> list[tuple[int, int]]:
    """1D bool 配列 (各列にcontentがあるか) から、 連続するTrue ブロックを抽出.
    gap_threshold 未満の False 区間は同じブロックとして統合."""
    runs: list[list[int]] = []
    in_run = False
    for x, v in enumerate(is_content_row):
        if v:
            if not in_run:
                runs.append([x, x])
                in_run = True
            else:
                runs[-1][1] = x
        else:
            in_run = False

    merged: list[list[int]] = []
    for r in runs:
        if merged and r[0] - merged[-1][1] - 1 < gap_threshold:
            merged[-1][1] = r[1]
        else:
            merged.append(list(r))

    return [(b[0], b[1]) for b in merged if (b[1] - b[0] + 1) >= min_block_width]


def analyze(
    image_path: str,
    rows: list[tuple[str, int, int]],
    *,
    x_start: int = 0,
    x_end: int | None = None,
    content_threshold: int = 230,
    gap_threshold: int = 3,
    min_block_width: int = 3,
    debug_out: str | None = None,
) -> dict:
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    arr = np.array(img)
    is_content = (arr.min(axis=2) < content_threshold)
    x_l = max(0, x_start)
    x_r = w if x_end is None else min(w, x_end)

    results: list[dict] = []
    for label, y_top, y_bot in rows:
        if y_top < 0 or y_bot >= h or y_top >= y_bot:
            results.append({"label": label, "error": f"invalid ROI: y_top={y_top}, y_bot={y_bot}"})
            continue
        strip = is_content[y_top : y_bot + 1, x_l:x_r]
        col_filled = strip.any(axis=0)
        blocks = find_blocks_in_row(
            col_filled,
            gap_threshold=gap_threshold,
            min_block_width=min_block_width,
        )
        if len(blocks) < 2:
            results.append(
                {
                    "label": label,
                    "y_top": y_top,
                    "y_bot": y_bot,
                    "n_blocks": len(blocks),
                    "blocks": blocks,
                    "error": "less than 2 blocks (need icon + text)",
                }
            )
            continue
        icon_left, icon_right = blocks[0]
        text_left, text_right = blocks[1]
        last_text_right = blocks[-1][1]
        results.append(
            {
                "label": label,
                "y_top": y_top,
                "y_bot": y_bot,
                "icon_left": int(icon_left + x_l),
                "icon_right": int(icon_right + x_l),
                "icon_width": int(icon_right - icon_left + 1),
                "text_left": int(text_left + x_l),
                "text_right_full": int(last_text_right + x_l),
                "gap_icon_to_text_px": int(text_left - icon_right - 1),
                "n_blocks": len(blocks),
            }
        )

    text_lefts = [r.get("text_left") for r in results if "text_left" in r]
    if not text_lefts:
        return {
            "ok": False,
            "error": "no valid rows with text",
            "image_size": (w, h),
            "rows": results,
        }
    min_left = min(text_lefts)
    max_left = max(text_lefts)
    delta_max = max_left - min_left

    result_dict: dict = {
        "ok": True,
        "image_size": (w, h),
        "rows": results,
        "text_left_min_px": int(min_left),
        "text_left_max_px": int(max_left),
        "delta_max_px": int(delta_max),
    }

    if debug_out:
        overlay = img.copy()
        draw = ImageDraw.Draw(overlay)
        for r in results:
            if "text_left" not in r:
                continue
            draw.rectangle(
                [r["icon_left"], r["y_top"], r["icon_right"], r["y_bot"]],
                outline=(255, 0, 0),
                width=2,
            )
            draw.rectangle(
                [r["text_left"], r["y_top"], r["text_right_full"], r["y_bot"]],
                outline=(0, 0, 255),
                width=2,
            )
            draw.line(
                [(r["text_left"], r["y_top"] - 5), (r["text_left"], r["y_bot"] + 5)],
                fill=(0, 200, 0),
                width=2,
            )
        Path(debug_out).parent.mkdir(parents=True, exist_ok=True)
        overlay.save(debug_out)
        result_dict["debug_out"] = debug_out

    return result_dict


def judge(result: dict, threshold: float) -> tuple[str, list[str]]:
    if not result.get("ok"):
        return "ERROR", [result.get("error", "unknown error")]
    details: list[str] = []
    delta_max = result["delta_max_px"]
    for r in result["rows"]:
        if "text_left" not in r:
            details.append(f"  {r['label']}: ERROR {r.get('error', '')}")
            continue
        details.append(
            f"  {r['label']}: text_left={r['text_left']}px gap_icon_to_text={r['gap_icon_to_text_px']}px"
        )
    details.append(f"  --- delta_max = {delta_max}px (threshold {threshold}px)")
    if delta_max <= threshold:
        return "ALL_ALIGNED", details
    return "SOME_NOT_ALIGNED", details


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", help="入力PNG画像のパス")
    p.add_argument(
        "--row",
        nargs=3,
        action="append",
        metavar=("LABEL", "Y_TOP", "Y_BOTTOM"),
        required=True,
        help="行ROI: ラベル, 上端y, 下端y. 複数指定可",
    )
    p.add_argument("--threshold", type=float, default=2.0, help="許容ずれ閾値 (px, default 2.0)")
    p.add_argument(
        "--gap-threshold",
        type=int,
        default=3,
        help="同じブロックとみなす空白列の最大数 (default 3)",
    )
    p.add_argument("--min-block-width", type=int, default=3)
    p.add_argument("--x-start", type=int, default=0, help="全 ROI の探索開始x座標 (左に余白/枠がある画像で指定)")
    p.add_argument("--x-end", type=int, default=None, help="全 ROI の探索終了x座標")
    p.add_argument("--debug-out", help="検出結果オーバーレイPNGの保存先")
    args = p.parse_args()

    rows = [(label, int(yt), int(yb)) for label, yt, yb in args.row]
    result = analyze(
        args.image,
        rows,
        x_start=args.x_start,
        x_end=args.x_end,
        gap_threshold=args.gap_threshold,
        min_block_width=args.min_block_width,
        debug_out=args.debug_out,
    )
    verdict, details = judge(result, args.threshold)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n=== VERDICT: {verdict} ===")
    for d in details:
        print(d)
    return 0 if verdict == "ALL_ALIGNED" else 1 if verdict == "SOME_NOT_ALIGNED" else 2


if __name__ == "__main__":
    sys.exit(main())
