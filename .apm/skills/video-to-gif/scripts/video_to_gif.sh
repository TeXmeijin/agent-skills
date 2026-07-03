#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  video_to_gif.sh INPUT_VIDEO [OUTPUT_GIF] [options]

Options:
  --start TIME       Start time, e.g. 00:00:02 or 2.5
  --duration SECS    Duration in seconds
  --width PX         Output width, default: 960
  --fps N            Output FPS, default: 12
  --dither MODE      paletteuse dither mode, default: bayer
  -h, --help         Show help

Example:
  video_to_gif.sh demo.mov demo.gif --start 1 --duration 6 --width 720 --fps 10
USAGE
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

input="$1"
shift

if [[ ! -f "$input" ]]; then
  echo "Input video not found: $input" >&2
  exit 1
fi

output=""
if [[ $# -gt 0 && "$1" != --* ]]; then
  output="$1"
  shift
fi

if [[ -z "$output" ]]; then
  base="${input%.*}"
  output="${base}.gif"
fi

start=""
duration=""
width="960"
fps="12"
dither="bayer"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start)
      start="${2:?--start requires a value}"
      shift 2
      ;;
    --duration)
      duration="${2:?--duration requires a value}"
      shift 2
      ;;
    --width)
      width="${2:?--width requires a value}"
      shift 2
      ;;
    --fps)
      fps="${2:?--fps requires a value}"
      shift 2
      ;;
    --dither)
      dither="${2:?--dither requires a value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

command -v ffmpeg >/dev/null 2>&1 || {
  echo "ffmpeg is required but was not found in PATH" >&2
  exit 1
}

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

palette="$tmp_dir/palette.png"
vf="fps=${fps},scale=${width}:-1:flags=lanczos"

trim_args=()
if [[ -n "$start" ]]; then
  trim_args+=(-ss "$start")
fi
if [[ -n "$duration" ]]; then
  trim_args+=(-t "$duration")
fi

ffmpeg -y "${trim_args[@]}" -i "$input" -vf "${vf},palettegen=stats_mode=diff" "$palette"
ffmpeg -y "${trim_args[@]}" -i "$input" -i "$palette" -lavfi "${vf} [x]; [x][1:v] paletteuse=dither=${dither}" -loop 0 "$output"

if command -v magick >/dev/null 2>&1; then
  magick "$output" -strip "$output"
fi

echo "$output"
