#!/usr/bin/env python3
"""Successful prior implementation pattern for a terminal screenshot.

This file is a reference, not a generic script to run unchanged. It shows the
pattern that worked: detect text lines, then define semantic redaction targets
as line indexes plus x-ranges.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from PIL import Image


REDACTIONS = [
    {"name": "top_account_context", "line": 0, "x1": 502, "x2": 716},
    {"name": "internal_file_path", "line": 9, "x1": 80, "x2": 549},
    {"name": "internal_class_name", "line": 12, "x1": 82, "x2": 562},
    {"name": "bottom_internal_namespace_1", "line": 18, "x1": 482, "x2": 942},
    {"name": "bottom_internal_namespace_2", "line": 19, "x1": 258, "x2": 577},
]


def find_text_lines(image_path: Path):
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
            lum = (r * 299 + g * 587 + b * 114) // 1000
            if diff > 45 and lum > 70:
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


def build_boxes(width, height, lines, y_pad=2, x_pad=2):
    boxes = []
    by_index = {line["index"]: line for line in lines}
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


def ffmpeg_filter(boxes, fill_color, border_color):
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
    args = parser.parse_args()

    width, height, bg, lines = find_text_lines(Path(args.image))
    boxes = build_boxes(width, height, lines)
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
        Path(args.json_path).write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        )
    if args.filter_path:
        Path(args.filter_path).write_text(result["ffmpeg_filter"] + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
