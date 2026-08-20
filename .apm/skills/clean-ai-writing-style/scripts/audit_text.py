#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


PATTERNS = {
    "否定・逆接": [
        r"ではない",
        r"ではなく",
        r"必要はない",
        r"とは限らない",
        r"ただし",
        r"一方で",
        r"逆に",
    ],
    "曖昧動詞": [
        r"寄る",
        r"寄せる",
        r"寄って",
        r"近い",
        r"つながる",
        r"繋がる",
        r"見える",
        r"感じる",
        r"担う",
        r"担って",
        r"関わる",
        r"関係する",
    ],
    "AI抽象名詞": [
        r"語彙",
        r"意思が出",
        r"意図が出",
        r"目的が出",
        r"判断が出",
    ],
    "衝突・攻撃比喩": [
        r"直撃",
        r"刺さる",
        r"刺さり",
        r"刺して",
        r"刺す",
    ],
    "評価語": [
        r"妥当",
        r"理想的",
        r"優先度",
        r"自然",
        r"素直",
        r"ずれ",
        r"成立",
    ],
    "擬人法": [
        r"名前が",
        r"名が",
        r"表が示",
        r"違いが現",
        r"構造が",
        r"流れが",
        r"文章が",
    ],
    "会話由来の唐突さ": [
        r"ここでいう",
        r"ここでは",
        r"この文脈では",
        r"きっかけ",
        r"切っ掛け",
        r"見たことがあります",
        r"事例として",
        r"面白かった",
    ],
    "見出しリスク": [
        r"^#{2,6}\s*.+とは$",
        r"^#{2,6}\s*.+について$",
        r"^#{2,6}\s*まず",
        r"^#{2,6}\s*全体像",
    ],
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit Japanese AI writing for known failure patterns."
    )
    parser.add_argument("file", type=Path)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    lines = args.file.read_text(encoding="utf-8").splitlines()
    start = max(args.start, 1)
    end = args.end or len(lines)
    selected = lines[start - 1 : end]

    print(f"# Writing audit: {args.file}")
    print(f"Range: {start}-{end}")
    print()

    total = 0
    for category, patterns in PATTERNS.items():
        hits = []
        compiled = [re.compile(pattern) for pattern in patterns]
        for offset, line in enumerate(selected, start=start):
            for pattern in compiled:
                if pattern.search(line):
                    hits.append((offset, line.strip(), pattern.pattern))
                    break

        print(f"## {category}")
        if not hits:
            print("- no hits")
        else:
            total += len(hits)
            for lineno, line, pattern in hits:
                print(f"- L{lineno}: `{line}`  (pattern: `{pattern}`)")
        print()

    print(f"Total hits: {total}")
    if total:
        print("Review every hit. A hit is not automatically wrong, but it must be justified.")


if __name__ == "__main__":
    main()
