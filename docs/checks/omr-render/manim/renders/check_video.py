"""Verify the actual MP4 and extract PNGs without opening desktop applications."""

import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


probe = run(
    "ffprobe",
    "-v",
    "error",
    "-count_frames",
    "-show_streams",
    "-show_format",
    "-of",
    "json",
    "out/video.mp4",
)
Path("renders/ffprobe.json").write_text(probe)
data = json.loads(probe)
assert len(data["streams"]) == 1, "Unexpected additional stream (including audio)"
video = data["streams"][0]
assert video["codec_type"] == "video" and video["codec_name"] == "h264"
assert (video["width"], video["height"]) == (640, 360)
assert video["r_frame_rate"] == video["avg_frame_rate"] == "30/1"
assert int(video["nb_read_frames"]) == 120
assert float(video["duration"]) == float(data["format"]["duration"]) == 4
run("ffmpeg", "-v", "error", "-xerror", "-i", "out/video.mp4", "-f", "null", "-")
frames = Path("renders/frames")
frames.mkdir(exist_ok=True)
run(
    "ffmpeg",
    "-v",
    "error",
    "-y",
    "-i",
    "out/video.mp4",
    "-map",
    "0:v:0",
    "-fps_mode",
    "passthrough",
    "-start_number",
    "0",
    str(frames / "frame-%03d.png"),
)
assert len(list(frames.glob("frame-*.png"))) == 120

# Original-resolution cells preserve legibility; labels use zero-based frame indices.
selected = [0, 7, 14, 15, 29, 30, 37, 44, 45, 59, 60, 67, 74, 75, 89, 90, 119]
sheet = Image.new("RGB", (1280, 390 * ((len(selected) + 1) // 2)), "#263340")
draw = ImageDraw.Draw(sheet)
for cell, frame in enumerate(selected):
    x, y = (cell % 2) * 640, (cell // 2) * 390
    with Image.open(frames / f"frame-{frame:03d}.png") as image:
        sheet.paste(image, (x, y + 30))
    draw.text((x + 12, y + 8), f"frame {frame:03d} | {frame / 30:.4f} s", fill="white")
sheet.save("renders/contact-sheet.png")
print("PASS: H.264, 640x360, 30 FPS, 120 decoded frames, 4 s, no audio streams.")
print("Extracted 120 real PNG frames; contact sheet contains 17 timeline samples.")
