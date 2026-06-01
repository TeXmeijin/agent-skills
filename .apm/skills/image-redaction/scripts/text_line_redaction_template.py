#!/usr/bin/env python3
"""Template for image-specific text redaction coordinate calculation.

Copy this script into the working project and edit REDACTIONS for the current
image. This is intentionally a starter, not a universal redaction engine.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from PIL import Image


# Replace with task-specific entries after inspecting detected line boxes.
# x1/x2 are horizontal pixel bounds on the target line.
REDACTIONS = [
    # {"name": "internal_path", "line": 3, "x1": 120, "x2": 480},
]


def find_text_lines(image_path: Path, diff_threshold: int, min_luma: int):
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size
    pixels = list(img.getdata())
    bg = Counter((r, g, b) for r, g, b, _ in pixels).most_common(1)[0][0]

    active_rows = []
    for y in range(height):
        xs = []
        for x in range(width):
            r, g, b, _ = img.getpixel((x, y))
            diff = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
            luma = (r * 299 + g * 587 + b * 114) // 1000
            if diff > diff_threshold and luma > min_luma:
                xs.append(x)
        if len(xs) >= 3:
            active_rows.append((y, min(xs), max(xs), len(xs)))

    groups = []
    current = []
    previous_y = None
    for row in active_rows:
        y = row[0]
        if previous_y is None or y <= previous_y + 1:
            current.append(row)
        else:
            groups.append(current)
            current = [row]
        previous_y = y
    if current:
        groups.append(current)

    lines = []
    for index, group in enumerate(groups):
        lines.append(
            {
                "index": index,
                "x1": min(row[1] for row in group),
                "x2": max(row[2] for row in group) + 1,
                "y1": group[0][0],
                "y2": group[-1][0] + 1,
                "text_pixels": sum(row[3] for row in group),
            }
        )
    return width, height, bg, lines


def build_boxes(width, height, lines, x_pad: int, y_pad: int):
    by_index = {line["index"]: line for line in lines}
    boxes = []
    for target in REDACTIONS:
        line = by_index[target["line"]]
        x = max(0, target["x1"] - x_pad)
        y = max(0, line["y1"] - y_pad)
        x2 = min(width, target["x2"] + x_pad)
        y2 = min(height, line["y2"] + y_pad)
        boxes.append(
            {
                "name": target["name"],
                "line": target["line"],
                "x": x,
                "y": y,
                "w": x2 - x,
                "h": y2 - y,
                "source_line_box": line,
            }
        )
    return boxes


def ffmpeg_filter(boxes, fill_color: str, border_color: str):
    parts = []
    for box in boxes:
        parts.append(
            f"drawbox=x={box['x']}:y={box['y']}:w={box['w']}:h={box['h']}:"
            f"color={fill_color}@1:t=fill"
        )
        parts.append(
            f"drawbox=x={box['x']}:y={box['y']}:w={box['w']}:h={box['h']}:"
            f"color={border_color}@1:t=1"
        )
    return ",".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--filter", dest="filter_path")
    parser.add_argument("--fill-color", default="0x5F6670")
    parser.add_argument("--border-color", default="0xD0C8B8")
    parser.add_argument("--diff-threshold", type=int, default=45)
    parser.add_argument("--min-luma", type=int, default=70)
    parser.add_argument("--x-pad", type=int, default=2)
    parser.add_argument("--y-pad", type=int, default=2)
    args = parser.parse_args()

    width, height, bg, lines = find_text_lines(
        Path(args.image), args.diff_threshold, args.min_luma
    )
    boxes = build_boxes(width, height, lines, args.x_pad, args.y_pad)
    result = {
        "image": args.image,
        "width": width,
        "height": height,
        "background_rgb": bg,
        "lines": lines,
        "boxes": boxes,
        "ffmpeg_filter": ffmpeg_filter(boxes, args.fill_color, args.border_color),
    }

    if args.json_path:
        Path(args.json_path).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if args.filter_path:
        Path(args.filter_path).write_text(result["ffmpeg_filter"] + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
