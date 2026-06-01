# Success Case: Terminal Screenshot Redaction

## Situation

The user had a screenshot intended for a public technical article. The screenshot showed terminal output from a coding-agent workflow. It contained useful context for the article, but also included internal names, file paths, and user-related details.

The user wanted a public-safe image without losing the meaning of the screenshot.

## What Worked

The successful flow was:

1. Preserve the original screenshot.
2. Write a dedicated Python coordinate-calculation script for that exact image.
3. Detect text-line bounding boxes from image pixels instead of guessing vertical rectangles.
4. Define redaction targets as semantic entries: target line index plus x-range.
5. Emit both JSON and an `ffmpeg` filter.
6. Render from the original image with `ffmpeg`.
7. Strip metadata with ImageMagick.
8. Show the output image inline.
9. Iterate by editing the script after the user said the first result was too broad.

The key correction was moving from manual large rectangles to calculated line-level boxes.

## Redaction Policy Used

The first acceptable version masked too much. The improved version kept public and explanatory context visible:

- Kept visible:
  - public organization or product names when the user explicitly said they were safe
  - Hook command shape
  - static-analysis tool and config shape
  - generic warning labels and module names when not sensitive
  - generic review-policy wording
  - generic `DTO` wording
- Masked:
  - user/account identifier context
  - internal file paths
  - internal fully-qualified class names
  - bottom-line internal namespace snippets

## General Notes

- Treat "public-safe" as a content policy decision. Do not automatically hide every company or tool name.
- Use a visibly different redaction color. Background-colored masks look like accidental smearing and make the edit untrustworthy.
- Keep y-coordinates tied to detected text-line boxes; avoid rectangles that touch neighboring rows.
- Re-render from the original image on every iteration.
- Keep generated JSON/filter files when they help audit what was masked.

## Representative Commands

```sh
python3 tools/calc_terminal_redactions.py input.png \
  --json output-redactions.json \
  --filter output-redactions.ffmpeg

FILTER="$(cat output-redactions.ffmpeg)"
ffmpeg -y -i input.png -map_metadata -1 -vf "$FILTER" -frames:v 1 output-redacted.png
magick output-redacted.png -strip output-redacted.png
```
