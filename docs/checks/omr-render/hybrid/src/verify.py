"""Decode actual delivery frames/audio; save reproducible measurements and PNGs."""

import hashlib
import json
from pathlib import Path
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
renders = root / "renders"
frames_dir = renders / "frames"
frames_dir.mkdir(exist_ok=True)


def run(*args):
    return subprocess.check_output(args, cwd=root)


def probe(path):
    return json.loads(
        run(
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            path,
        )
    )


delivery = probe("out/video.mp4")
insert = probe("renders/insert.mp4")
video = delivery["streams"][0]
assert (
    video["width"],
    video["height"],
    video["nb_read_frames"],
    video["r_frame_rate"],
) == (640, 360, "120", "30/1")
assert len(insert["streams"]) == 1 and insert["streams"][0]["nb_read_frames"] == "60"
run("ffmpeg", "-v", "error", "-xerror", "-i", "out/video.mp4", "-f", "null", "-")
raw = run(
    "ffmpeg",
    "-v",
    "error",
    "-i",
    "out/video.mp4",
    "-f",
    "rawvideo",
    "-pix_fmt",
    "rgb24",
    "-",
)
frames = np.frombuffer(raw, np.uint8).reshape(-1, 360, 640, 3)
selected = [0, 29, 30, 44, 45, 60, 74, 75, 89, 90, 119]
sheet = Image.new("RGB", (1280, 390 * 6), "#202830")
draw = ImageDraw.Draw(sheet)
for i, frame in enumerate(selected):
    image = Image.fromarray(frames[frame])
    image.save(frames_dir / f"frame-{frame:03d}.png")
    x, y = (i % 2) * 640, (i // 2) * 390
    sheet.paste(image, (x, y + 30))
    draw.text((x + 12, y + 8), f"frame {frame} / {frame / 30:.4f} s", fill="white")
sheet.save(renders / "contact-sheet.png")

# Track both separated dots across EVERY actual final video frame in the insert.
positions = []
for n in range(30, 90):
    f = frames[n].astype(float)
    mask = (f[:, :, 1] > 140) & (f[:, :, 1] > f[:, :, 0] * 1.4) & (f[:, :, 2] > 90)
    centers = []
    for lo, hi in [(0, 320), (320, 640)]:
        yy, xx = np.where(mask[:, lo:hi])
        assert len(xx) > 400
        centers.append([float(xx.mean() + lo), float(yy.mean())])
    positions.append({"frame": n, "centers": centers})
left = [p["centers"][0][0] for p in positions]
assert np.all(np.diff(left) >= -0.2)

audio = np.frombuffer(
    run(
        "ffmpeg",
        "-v",
        "error",
        "-i",
        "out/video.mp4",
        "-vn",
        "-ac",
        "2",
        "-ar",
        "48000",
        "-f",
        "f32le",
        "-",
    ),
    dtype="<f4",
)
stereo = audio.reshape(-1, 2)
audio = stereo[:, 0]  # Actual channel; a mono downmix would add about 3 dB.
with wave.open(str(root / "public/tone.wav")) as wav:
    source = (
        np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(float)
        / 32768
    )
active = np.flatnonzero(np.abs(audio) > 0.001)
segment = audio[144000:153600]
spectrum = np.abs(np.fft.rfft(segment))
frequency = float(np.fft.rfftfreq(len(segment), 1 / 48000)[spectrum.argmax()])
assert frequency == 660
assert abs(active[0] / 48000 - 3) < 0.01
assert abs((active[-1] + 1) / 48000 - 3.2) < 0.01
metrics = {
    "delivery": delivery,
    "insert": insert,
    "sha256": {
        p: hashlib.sha256((root / p).read_bytes()).hexdigest()
        for p in ["requirements.md", "content/index.md", "script.md", "out/video.mp4"]
    },
    "audio": {
        "decoded_samples": len(audio),
        "decoded_duration": len(audio) / 48000,
        "channel_peaks_fs": np.abs(stereo).max(axis=0).tolist(),
        "signal_threshold_fs": 0.001,
        "active_start_s": float(active[0] / 48000),
        "active_end_s": float((active[-1] + 1) / 48000),
        "peak_fs": float(np.abs(audio).max()),
        "rms_signal_fs": float(np.sqrt(np.mean(segment**2))),
        "peak_before_2_99_s": float(np.abs(audio[:143520]).max()),
        "peak_after_3_21_s": float(np.abs(audio[154080:]).max()),
        "dominant_hz": frequency,
        "source_peak_fs": float(np.abs(source).max()),
        "source_duration": len(source) / 48000,
        "source_correlation_at_3s": float(np.corrcoef(source, segment)[0, 1]),
        "source_vs_decoded_gain": float(
            np.dot(segment, source) / np.dot(source, source)
        ),
    },
    "dot_positions": positions,
    "background_rgb": {str(n): frames[n, 20, 20].tolist() for n in selected},
}
(renders / "measurements.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(
    json.dumps(
        {
            "audio": metrics["audio"],
            "background_rgb": metrics["background_rgb"],
            "dot_samples": [positions[i] for i in [0, 14, 30, 45, 59]],
        },
        indent=2,
    )
)
