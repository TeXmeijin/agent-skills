---
name: video-to-gif
description: Convert local video files into publication-ready GIFs. Use when the user asks to make a GIF from a screen recording or video file, reduce GIF size, crop/trim/scale a clip, optimize animation output, or prepare a short video for sharing in Markdown, GitHub, Zenn, docs, or chat.
---

# Video To GIF

## Core Workflow

Use `ffmpeg` for conversion. Prefer a two-pass palette workflow because it keeps GIFs smaller and cleaner than direct video-to-GIF conversion.

1. Confirm the input video path exists.
2. Decide trim range, width, and FPS from the user's goal.
3. Generate a palette from the source clip.
4. Render the GIF with the palette.
5. Check file size and visual quality.
6. If the output is too large, reduce width, FPS, duration, or dither strength.
7. Return the absolute output path and embed the GIF when the environment supports it.

Use `scripts/video_to_gif.sh` for standard conversions instead of rewriting the ffmpeg pipeline each time.

## Defaults

- FPS: `12`
- Width: `960`
- Output path: source filename with `.gif`
- Trim: full video unless the user specifies start/end or duration
- Scaling: preserve aspect ratio

For UI demos, `10-15fps` is usually enough. For terminal recordings, `8-12fps` is often better and much smaller.

## Standard Command

```sh
./scripts/video_to_gif.sh input.mov output.gif --start 00:00:02 --duration 5 --width 960 --fps 12
```

From this skill directory:

```sh
SKILL_DIR="/path/to/video-to-gif"
"$SKILL_DIR/scripts/video_to_gif.sh" input.mov output.gif --width 960 --fps 12
```

## Size Reduction Strategy

Apply these in order:

1. Trim dead time at the start/end.
2. Reduce width to `720` or `640`.
3. Reduce FPS to `10` or `8`.
4. Use a shorter clip instead of trying to optimize a long one.

Avoid huge GIFs for documentation. If the output remains too large after reasonable trimming and scaling, suggest MP4/WebM instead.

## Verification

After conversion:

```sh
ls -lh output.gif
ffprobe -v error -show_entries stream=width,height,nb_frames,duration -of default=nw=1 output.gif
```

If possible, inspect the GIF visually before finalizing.
