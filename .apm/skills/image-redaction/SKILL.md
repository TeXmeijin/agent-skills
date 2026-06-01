---
name: image-redaction
description: Create publication-safe redacted images from screenshots or other images that contain internal, private, or company-specific text. Use when the user asks to mask, redact, hide, anonymize, or sanitize sensitive information in an attached/local image, especially when they want selective text masking, public-release screenshots, article images, or iterative "消しすぎ/もっと隠して" adjustment. Always prefer writing a purpose-built script for the specific image before running ffmpeg/ImageMagick, rather than manually guessing rectangles.
---

# Image Redaction

## Core Rule

For every real redaction task, write or adapt a small dedicated script for that exact image before producing the final image.

Do not rely on ad hoc visual rectangle guesses alone. The desired workflow is:

1. Inspect the image and the user's disclosure policy.
2. Decide what categories should remain visible and what categories must be masked.
3. Write a task-local Python script that calculates precise coordinates from the image, preferably using detected text-line pixel bounds.
4. Run the script to emit machine-readable redaction boxes and an `ffmpeg` filter string.
5. Run `ffmpeg` or ImageMagick to render the redacted image.
6. Strip metadata.
7. Show the generated image in the thread.
8. Iterate by editing the script's redaction targets, not by freehand changing the image.

## Redaction Judgment

Treat masking as an editorial decision, not just an image operation.

- Preserve context that helps the image support the article or explanation.
- Keep public facts visible when the user says they are safe, such as a public company name or product name.
- Mask internal file paths, private class names, account/user IDs, customer/student/teacher identifiers, private repository names, tokens, hostnames, emails, secrets, and unreleased operational details.
- If the user says "消しすぎ", restore low-risk context first: public organization names, generic tool names, command names, generic error framing.
- If the user says "もっと隠して", add narrower masks around the specific remaining sensitive text instead of blanketing whole rows unless the whole row is sensitive.

Use visible redaction styling. A mask should be clearly identifiable as intentional redaction:

- Prefer a neutral gray fill that contrasts with the background.
- Add a thin border when the background is dark or low contrast.
- Avoid matching the background color unless the user explicitly wants seamless removal.

## Script Pattern

Create a script under the current project, temporary directory, or output folder. Prefer names like:

- `tools/calc_<image_slug>_redactions.py`
- `tmp/calc_redactions.py`
- `attachments/<image_slug>-redactions.py`

The script should usually:

- Load the image with Pillow.
- Detect the dominant background color.
- Detect text rows by comparing pixels against the background.
- Group contiguous active rows into line boxes.
- Define a small `REDACTIONS` list with semantic names, line indexes, and x-ranges.
- Expand each box by only a small padding, such as 1-3 pixels.
- Emit:
  - JSON containing source image size, detected line boxes, redaction boxes, and labels
  - an `ffmpeg` `drawbox` filter string

Use `scripts/text_line_redaction_template.py` as a starter, but customize it per image. The template is not a one-size-fits-all final solution.

## Rendering

Render with `ffmpeg` when possible:

```sh
FILTER="$(cat path/to/redactions.ffmpeg)"
ffmpeg -y -i input.png -map_metadata -1 -vf "$FILTER" -frames:v 1 output-redacted.png
magick output-redacted.png -strip output-redacted.png
```

If `ffmpeg` warns that the output filename does not contain a sequence pattern but still writes the image, this is acceptable. Use `-update 1` only if the local ffmpeg build requires it.

For final answers in Codex Desktop, embed the output image with an absolute path:

```markdown
![マスク済み画像](/absolute/path/to/output-redacted.png)
```

## Iteration Workflow

When the user critiques the result:

- Update the script's `REDACTIONS` policy or x-ranges.
- Re-run the script.
- Re-render the image from the original source.
- Do not edit the already-redacted image as the new source.

Keep earlier generated outputs if useful, but make the latest intended output path clear.

## References

- Read `references/success-case-terminal-redaction.md` when handling screenshots with terminal text, code paths, or article-publication redaction.
- Use `references/success-case-line_redactions.py` as a concrete successful prior implementation pattern from a real thread, with private details removed.
