#!/usr/bin/env python3
"""
命題: 画像左の円形アイコンと、 その右に並ぶ要素群の縦中心 y が揃っているか.

これは centering-judge skill の「参考実装」のひとつ。 そのまま呼んで使うための
固定ツールではない。 命題が違えば別スクリプトを書くこと。

主要仮定:
  - 画像幅の左 8-20% に 1 つだけ円形要素 (aspect 0.7-1.4, circularity ≥ 1.2) がある
  - その右側 20-95% に揃えるべき要素群が縦 1 行で並ぶ

アルゴリズム:
  1. 背景マスク: RGB 最小値 < 230 を content とみなす
  2. avatar 検出: 左 zone で aspect/circularity 条件を満たす最良 score の縦 run
  3. 右側要素検出: avatar の縦範囲 ± vertical_margin、 右側 zone で縦方向 content
     profile を作り、 0連続 gap が cluster_merge_x_gap 以上で要素境界とみなす
  4. 各要素の bbox 中心 y を avatar 中心 y と比較、 |delta| > threshold で FAIL

Usage:
    python3 left_circle_vs_right_row_center_y.py <image.png> [--threshold 3.0] [--debug-out <path>]

Exit codes:
    0: ALL CENTERED
    1: SOME NOT CENTERED
    2: ERROR
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


def find_runs(mask: np.ndarray, min_len: int, max_len: int) -> list[tuple[int, int]]:
    """1D bool 配列から連続するTrue区間を抽出. (start, end_exclusive)を返す."""
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for i, v in enumerate(mask):
        if v:
            if start is None:
                start = i
        else:
            if start is not None:
                length = i - start
                if min_len <= length <= max_len:
                    runs.append((start, i))
                start = None
    if start is not None:
        length = len(mask) - start
        if min_len <= length <= max_len:
            runs.append((start, len(mask)))
    return runs


def detect_avatar(
    is_content: np.ndarray,
    *,
    avatar_zone_left_ratio: float,
    avatar_zone_right_ratio: float,
    min_avatar_height: int,
    max_avatar_height: int,
    row_content_min_pixels: int,
) -> tuple[dict | None, list, tuple[int, int]]:
    h, w = is_content.shape
    az_l = int(w * avatar_zone_left_ratio)
    az_r = int(w * avatar_zone_right_ratio)
    avatar_strip = is_content[:, az_l:az_r]
    avatar_per_row = avatar_strip.sum(axis=1)
    avatar_row_mask = avatar_per_row > row_content_min_pixels
    runs = find_runs(avatar_row_mask, min_len=min_avatar_height, max_len=max_avatar_height)
    if not runs:
        return None, [], (az_l, az_r)

    candidates = []
    for top, bottom_excl in runs:
        bottom = bottom_excl - 1
        height = bottom - top + 1
        widths = avatar_per_row[top:bottom_excl].astype(float)
        if widths.max() == 0:
            continue
        max_w = float(widths.max())
        mid = len(widths) // 2
        center_avg = (
            widths[mid - height // 6 : mid + height // 6 + 1].mean() if height >= 6 else max_w
        )
        edge_avg = (widths[: max(1, height // 4)].mean() + widths[-max(1, height // 4) :].mean()) / 2.0
        circularity = float(center_avg / edge_avg) if edge_avg > 0 else float("inf")
        aspect = max_w / height
        aspect_score = 1.0 / (1.0 + abs(aspect - 1.0))
        score = aspect_score * min(circularity / 1.5, 2.0)
        candidates.append(
            {
                "top": int(top),
                "bottom": int(bottom),
                "height": int(height),
                "max_width": int(max_w),
                "aspect": float(aspect),
                "circularity": float(circularity),
                "score": float(score),
            }
        )

    avatar_candidates = [
        c for c in candidates if 0.7 <= c["aspect"] <= 1.4 and c["circularity"] >= 1.2
    ]
    if not avatar_candidates:
        avatar_candidates = sorted(candidates, key=lambda c: -c["score"])[:1]
    if not avatar_candidates:
        return None, candidates, (az_l, az_r)
    avatar = sorted(avatar_candidates, key=lambda c: -c["score"])[0]
    return avatar, candidates, (az_l, az_r)


def detect_right_elements(
    is_content: np.ndarray,
    *,
    avatar_top: int,
    avatar_bottom: int,
    right_zone_left: int,
    right_zone_right: int,
    vertical_margin: int,
    min_area: int,
    cluster_merge_x_gap: int,
) -> list[dict]:
    """avatar 縦範囲(マージン拡張)・右側 zone 内で content を「視覚的な要素」単位に分割する.

    手法: 縦方向の content profile (各 x列の content pixel数) を作り、 0連続gap が
    cluster_merge_x_gap 以上のとき要素境界とみなす. これにより文字片の連結成分が
    水平方向で近接しているところは1要素として統合され、 明確な空白列で区切られている
    バッジ等は別要素として分離される."""
    h, w = is_content.shape
    y_top = max(0, avatar_top - vertical_margin)
    y_bottom = min(h - 1, avatar_bottom + vertical_margin)
    sub = is_content[y_top : y_bottom + 1, right_zone_left:right_zone_right]

    # 縦方向 content profile
    col_profile = sub.sum(axis=0)  # 長さ = right_zone_right - right_zone_left
    is_col_filled = col_profile > 0

    # 連続するTrue区間(=要素) を抽出. False(空白)が cluster_merge_x_gap 以上続いたら境界
    clusters: list[dict] = []
    start = None
    last_filled = None
    for i, v in enumerate(is_col_filled):
        if v:
            if start is None:
                start = i
            last_filled = i
        else:
            if start is not None and last_filled is not None:
                if (i - last_filled - 1) >= cluster_merge_x_gap:
                    clusters.append({"left_local": start, "right_local": last_filled})
                    start = None
                    last_filled = None
    if start is not None and last_filled is not None:
        clusters.append({"left_local": start, "right_local": last_filled})

    # 各 cluster の bbox 縦範囲を sub から計測
    result: list[dict] = []
    for cl in clusters:
        ll, lr = cl["left_local"], cl["right_local"]
        block = sub[:, ll : lr + 1]
        rows_with_content = np.where(block.any(axis=1))[0]
        if len(rows_with_content) == 0:
            continue
        bbox_top = int(rows_with_content.min()) + y_top
        bbox_bottom = int(rows_with_content.max()) + y_top
        bbox_left = ll + right_zone_left
        bbox_right = lr + right_zone_left
        area = int(block.sum())
        if area < min_area:
            continue
        result.append(
            {
                "top": bbox_top,
                "bottom": bbox_bottom,
                "left": bbox_left,
                "right": bbox_right,
                "area": area,
                "n_components": 1,
            }
        )
    return result


def analyze(
    image_path: str,
    *,
    avatar_zone_left_ratio: float = 0.08,
    avatar_zone_right_ratio: float = 0.20,
    right_zone_right_ratio: float = 0.95,
    min_avatar_height: int = 30,
    max_avatar_height: int = 120,
    content_threshold: int = 230,
    row_content_min_pixels: int = 5,
    vertical_margin: int = 40,
    min_element_area: int = 50,
    cluster_merge_x_gap: int = 30,
    debug_out: str | None = None,
) -> dict:
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    arr = np.array(img)
    is_content = (arr.min(axis=2) < content_threshold).astype(np.uint8)

    avatar, all_candidates, avatar_zone_px = detect_avatar(
        is_content,
        avatar_zone_left_ratio=avatar_zone_left_ratio,
        avatar_zone_right_ratio=avatar_zone_right_ratio,
        min_avatar_height=min_avatar_height,
        max_avatar_height=max_avatar_height,
        row_content_min_pixels=row_content_min_pixels,
    )
    if avatar is None:
        return {
            "ok": False,
            "error": "no avatar-shape vertical run found in left zone",
            "image_size": (w, h),
            "avatar_zone_px": avatar_zone_px,
            "all_run_candidates": all_candidates,
        }

    avatar_top = avatar["top"]
    avatar_bottom = avatar["bottom"]
    avatar_center_y = (avatar_top + avatar_bottom) / 2.0

    right_zone_left = avatar_zone_px[1]
    right_zone_right = int(w * right_zone_right_ratio)

    clusters = detect_right_elements(
        is_content,
        avatar_top=avatar_top,
        avatar_bottom=avatar_bottom,
        right_zone_left=right_zone_left,
        right_zone_right=right_zone_right,
        vertical_margin=vertical_margin,
        min_area=min_element_area,
        cluster_merge_x_gap=cluster_merge_x_gap,
    )

    # 各クラスタの中心 y と avatar center との差分
    elements = []
    for idx, cl in enumerate(clusters):
        center_y = (cl["top"] + cl["bottom"]) / 2.0
        delta = center_y - avatar_center_y
        elements.append(
            {
                "id": f"element{idx}",
                "left": cl["left"],
                "right": cl["right"],
                "top": cl["top"],
                "bottom": cl["bottom"],
                "center_y": float(center_y),
                "width_px": cl["right"] - cl["left"] + 1,
                "height_px": cl["bottom"] - cl["top"] + 1,
                "delta_minus_avatar_center_px": float(delta),
                "n_components": cl["n_components"],
            }
        )

    result: dict = {
        "ok": True,
        "image_size": (w, h),
        "avatar_zone_px": avatar_zone_px,
        "right_zone_px": (right_zone_left, right_zone_right),
        "avatar": {
            "top": int(avatar_top),
            "bottom": int(avatar_bottom),
            "center_y": float(avatar_center_y),
            "height_px": avatar_bottom - avatar_top + 1,
            "aspect": float(avatar["aspect"]),
            "circularity": float(avatar["circularity"]),
        },
        "elements": elements,
        "n_elements": len(elements),
    }

    if debug_out:
        overlay = img.copy()
        draw = ImageDraw.Draw(overlay)
        draw.rectangle(
            [avatar_zone_px[0], avatar_top, avatar_zone_px[1], avatar_bottom],
            outline=(255, 0, 0),
            width=2,
        )
        draw.line([(0, avatar_center_y), (w, avatar_center_y)], fill=(255, 0, 0), width=1)
        palette = [(0, 0, 255), (0, 150, 0), (180, 0, 180), (200, 100, 0), (0, 150, 150)]
        for idx, el in enumerate(elements):
            color = palette[idx % len(palette)]
            draw.rectangle([el["left"], el["top"], el["right"], el["bottom"]], outline=color, width=2)
            draw.line([(0, el["center_y"]), (w, el["center_y"])], fill=color, width=1)
        Path(debug_out).parent.mkdir(parents=True, exist_ok=True)
        overlay.save(debug_out)
        result["debug_out"] = debug_out

    return result


def judge(result: dict, threshold: float) -> tuple[str, list[str]]:
    if not result.get("ok"):
        return "ERROR", [result.get("error", "unknown error")]
    details: list[str] = []
    not_centered_any = False
    for el in result["elements"]:
        delta = el["delta_minus_avatar_center_px"]
        if abs(delta) > threshold:
            direction = "below" if delta > 0 else "above"
            details.append(
                f"  {el['id']} (x={el['left']}-{el['right']}, w={el['width_px']}px): "
                f"{abs(delta):.2f}px {direction} avatar center (NOT CENTERED)"
            )
            not_centered_any = True
        else:
            details.append(
                f"  {el['id']} (x={el['left']}-{el['right']}, w={el['width_px']}px): "
                f"|delta|={abs(delta):.2f}px <= {threshold}px (centered)"
            )
    verdict = "SOME_NOT_CENTERED" if not_centered_any else "ALL_CENTERED"
    return verdict, details


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", help="入力PNG画像のパス")
    p.add_argument("--threshold", type=float, default=3.0, help="許容ずれ閾値 (px, default 3.0)")
    p.add_argument("--debug-out", help="検出結果オーバーレイPNGの保存先")
    p.add_argument(
        "--avatar-zone",
        nargs=2,
        type=float,
        default=[0.08, 0.20],
        metavar=("LEFT_RATIO", "RIGHT_RATIO"),
        help="アバター探索の左右比率 (default 0.08 0.20)",
    )
    p.add_argument(
        "--right-zone-right",
        type=float,
        default=0.95,
        help="右側要素探索の右端比率 (default 0.95)",
    )
    p.add_argument("--min-avatar-height", type=int, default=30)
    p.add_argument(
        "--max-avatar-height",
        type=int,
        default=120,
        help="retina @2x スクショなら 150 程度に",
    )
    p.add_argument("--vertical-margin", type=int, default=40, help="avatar の縦範囲を上下に拡張するマージン (px)")
    p.add_argument("--min-element-area", type=int, default=50, help="連結成分の最小面積")
    p.add_argument(
        "--cluster-merge-x-gap",
        type=int,
        default=30,
        help="水平方向に近接する成分を統合する gap 閾値 (px)",
    )
    args = p.parse_args()

    result = analyze(
        args.image,
        avatar_zone_left_ratio=args.avatar_zone[0],
        avatar_zone_right_ratio=args.avatar_zone[1],
        right_zone_right_ratio=args.right_zone_right,
        min_avatar_height=args.min_avatar_height,
        max_avatar_height=args.max_avatar_height,
        vertical_margin=args.vertical_margin,
        min_element_area=args.min_element_area,
        cluster_merge_x_gap=args.cluster_merge_x_gap,
        debug_out=args.debug_out,
    )
    verdict, details = judge(result, args.threshold)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n=== VERDICT: {verdict} ===")
    for d in details:
        print(d)
    return 0 if verdict == "ALL_CENTERED" else 1 if verdict == "SOME_NOT_CENTERED" else 2


if __name__ == "__main__":
    sys.exit(main())
