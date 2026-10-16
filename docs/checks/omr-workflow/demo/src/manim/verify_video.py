"""УЧЕБНЫЙ headless-контроль: декодирование всех кадров и PNG из MP4."""

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw


def main():
    video = Path("out/video.mp4")
    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-count_frames",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(video),
            ]
        )
    )
    Path("renders/probe.json").write_text(json.dumps(probe, indent=2) + "\n")
    assert len(probe["streams"]) == 1, "Unexpected audio/other stream"
    stream = probe["streams"][0]
    assert (stream["width"], stream["height"]) == (640, 360)
    assert stream["r_frame_rate"] == stream["avg_frame_rate"] == "30/1"
    assert int(stream["nb_read_frames"]) == 120
    assert float(probe["format"]["duration"]) == 4

    raw = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-xerror",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ]
    )
    frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 360, 640, 3)
    assert len(frames) == 120
    # Quantify compression noise separately from an actual visual change.
    deltas = np.abs(frames[1:].astype(np.int16) - frames[:-1].astype(np.int16))
    mae = deltas.mean(axis=(1, 2, 3))
    changes = (np.flatnonzero(mae > 0.1) + 1).tolist()
    assert changes == [60], changes

    selected = [0, 30, 58, 59, 60, 61, 90, 119]
    sheet = Image.new("RGB", (1280, 4 * 390), "#202020")
    draw = ImageDraw.Draw(sheet)
    bounds = {}
    for position, index in enumerate(selected):
        image = Image.fromarray(frames[index])
        image.save(f"renders/keyframes/frame-{index:03d}.png")
        x, y = (position % 2) * 640, (position // 2) * 390
        sheet.paste(image, (x, y + 30))
        draw.text((x + 12, y + 8), f"frame {index} / {index / 30:.4f} s", fill="white")
        # Ignore low-amplitude ringing from lossy H.264 at the glyph edges.
        mask = frames[index].max(axis=2) > 64
        ys, xs = np.where(mask)
        bounds[str(index)] = [
            int(xs.min()),
            int(ys.min()),
            int(xs.max()) + 1,
            int(ys.max()) + 1,
        ]
        assert xs.min() >= 32 and xs.max() < 608
        assert ys.min() >= 32 and ys.max() < 328
    sheet.save("renders/keyframes/contact-sheet.png")

    result = {
        "decoded_frames": len(frames),
        "scene_change_frames_mae_over_0.1": changes,
        "cut_mae_rgb": float(mae[59]),
        "max_within_scene_adjacent_mae_rgb": float(np.delete(mae, 59).max()),
        "unique_decoded_rgb_frames_per_scene": [
            len({hashlib.sha256(frame.tobytes()).hexdigest() for frame in block})
            for block in (frames[:60], frames[60:])
        ],
        "visible_bounds_threshold_64_exclusive_right_bottom": bounds,
        "video_sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
    }
    Path("renders/checks.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
