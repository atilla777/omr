"""Inspect the actual encoded MP4; no desktop windows or audio playback."""

import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import wave

root = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.check_output(args, cwd=root)


probe = json.loads(
    run(
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
)
(root / "renders/probe.json").write_text(json.dumps(probe, indent=2))
run("ffmpeg", "-v", "error", "-i", "out/video.mp4", "-f", "null", "-")
frames = [0, 9, 59, 60, 61, 65, 69, 119]
frame_dir = root / "renders/frames"
frame_dir.mkdir(exist_ok=True)
pixels = []
for frame in frames:
    run(
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        "out/video.mp4",
        "-vf",
        rf"select=eq(n\,{frame})",
        "-frames:v",
        "1",
        f"renders/frames/frame-{frame:03}.png",
    )
    rgb = run(
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"renders/frames/frame-{frame:03}.png",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    )
    bg = tuple(rgb[:3])
    points = [
        (i // 3 % 640, i // 3 // 640)
        for i in range(0, len(rgb), 3)
        if max(abs(rgb[i + j] - bg[j]) for j in range(3)) > 20
    ]
    bbox = (
        [
            min(p[0] for p in points),
            min(p[1] for p in points),
            max(p[0] for p in points),
            max(p[1] for p in points),
        ]
        if points
        else None
    )
    pixels.append(
        {"frame": frame, "background_rgb": bg, "text_bbox_threshold_20": bbox}
    )

run(
    "ffmpeg",
    "-v",
    "error",
    "-y",
    "-i",
    "out/video.mp4",
    "-vf",
    "select=" + "+".join(f"eq(n\\,{f})" for f in frames) + ",scale=320:180,tile=4x2",
    "-frames:v",
    "1",
    "renders/contact-sheet.png",
)
raw = run(
    "ffmpeg",
    "-v",
    "error",
    "-i",
    "out/video.mp4",
    "-map",
    "0:a:0",
    "-ar",
    "48000",
    "-f",
    "f32le",
    "-",
)
interleaved = array.array("f", raw)
audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
channels = audio["channels"]
samples = interleaved[0::channels]
rate = 48000


def stats(start, end):
    data = samples[round(start * rate) : round(end * rate)]
    peak = max(map(abs, data), default=0)
    rms = math.sqrt(sum(x * x for x in data) / len(data)) if data else 0
    return {
        "peak": peak,
        "rms": rms,
        "peak_dbfs": 20 * math.log10(peak) if peak else None,
    }


active = [i for i, x in enumerate(samples) if abs(x) > 0.001]
middle = samples[round(2.02 * rate) : round(2.18 * rate)]
crossings = [i for i in range(1, len(middle)) if middle[i - 1] <= 0 < middle[i]]
frequency = (len(crossings) - 1) * rate / (crossings[-1] - crossings[0])
with wave.open(str(root / "public/tone.wav")) as wav:
    source = array.array("h", wav.readframes(wav.getnframes()))
    source_info = {
        "samples": len(source),
        "rate": wav.getframerate(),
        "channels": wav.getnchannels(),
        "sample_width": wav.getsampwidth(),
        "peak": max(map(abs, source)) / 32768,
    }
result = {
    "video_sha256": hashlib.sha256((root / "out/video.mp4").read_bytes()).hexdigest(),
    "source_tone": source_info,
    "decoded_audio_samples_per_channel": len(samples),
    "decoded_audio_peak_per_channel": [
        max(map(abs, interleaved[c::channels])) for c in range(channels)
    ],
    "audio_measurement_channel": 0,
    "decoded_audio_duration": len(samples) / rate,
    "active_above_minus60dbfs": [active[0] / rate, active[-1] / rate],
    "frequency_hz_zero_crossings": frequency,
    "audio_windows": {
        f"{a}-{b}s": stats(a, b)
        for a, b in [
            (0, 1.98),
            (1.98, 2),
            (2, 2.01),
            (2.02, 2.18),
            (2.19, 2.2),
            (2.2, 2.22),
            (2.22, 4),
        ]
    },
    "frames": pixels,
}
(root / "renders/measurements.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
video = next(s for s in probe["streams"] if s["codec_type"] == "video")
assert (
    video["width"],
    video["height"],
    video["r_frame_rate"],
    video["nb_read_frames"],
) == (640, 360, "30/1", "120")
assert video["duration"] == "4.000000"
assert abs(frequency - 660) < 1
assert 1.999 < active[0] / rate < 2.005 and 2.195 < active[-1] / rate < 2.205
assert stats(0, 1.98)["peak"] < 0.0001 and stats(2.22, 4)["peak"] < 0.0001
print("Video, tone timing, frequency and silence checks passed.")
