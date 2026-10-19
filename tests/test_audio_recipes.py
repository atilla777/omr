"""Numerical checks of omr-audio recipes, not a listening/agent evaluation.

Run: python3 -m unittest discover -s tests -p 'test_audio_recipes.py' -v
Requires ffmpeg/ffprobe, libx264 and aac. No downloads or third-party Python.
Generated signals/media live only in a TemporaryDirectory (respects TMPDIR).
"""

import array
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


COMPRESSOR = "acompressor=threshold=0.125:ratio=2:attack=15:release=150:makeup=1"
TARGET = "I=-16:TP=-1.5:LRA=11"
RATE = 48000


def run(*args):
    return subprocess.run([str(arg) for arg in args], capture_output=True, check=True)


def ffmpeg(*args):
    return run("ffmpeg", "-nostdin", "-hide_banner", "-n", *args)


def levels(path):
    result = ffmpeg(
        "-i",
        path,
        "-map",
        "0:a:0",
        "-af",
        f"loudnorm={TARGET}:print_format=json",
        "-f",
        "null",
        "-",
    ).stderr.decode()
    return json.JSONDecoder().raw_decode(result[result.rindex("{") :])[0]


def samples(path):
    raw = ffmpeg(
        "-v",
        "error",
        "-i",
        path,
        "-map",
        "0:a:0",
        "-c:a",
        "pcm_f32le",
        "-f",
        "f32le",
        "-",
    ).stdout
    values = array.array("f", raw)
    if sys.byteorder != "little":
        values.byteswap()
    return values


def rms(values, start, end):
    section = values[int(start * RATE) : int(end * RATE)]
    return math.sqrt(sum(value * value for value in section) / len(section))


def contrast(values):
    return 20 * math.log10(rms(values, 3.5, 5.5) / rms(values, 0.5, 2.5))


class AudioRecipes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all(shutil.which(name) for name in ("ffmpeg", "ffprobe")):
            raise RuntimeError("Install ffmpeg and ffprobe before running checks")
        cls.temporary = tempfile.TemporaryDirectory(prefix="omr-audio-check-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.source = cls.root / "input.wav"
        pcm = array.array("h")
        for index in range(12 * RATE):
            second = index / RATE
            amplitude = 0.04 if second < 3 or second >= 9 else 0.4
            if 6 <= second < 9:
                amplitude = 0
            pcm.append(round(32767 * amplitude * math.sin(2 * math.pi * 440 * second)))
        if sys.byteorder != "little":
            pcm.byteswap()
        with wave.open(str(cls.source), "wb") as output:
            output.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
            output.writeframes(pcm.tobytes())
        cls.original_hash = hashlib.sha256(cls.source.read_bytes()).hexdigest()

    def tearDown(self):
        self.assertEqual(
            hashlib.sha256(self.source.read_bytes()).hexdigest(), self.original_hash
        )

    def test_gain_vs_compression_and_silence(self):
        gained = self.root / "gained.wav"
        compressed = self.root / "prepared.wav"
        for dest, effect in ((gained, "volume=-6dB"), (compressed, COMPRESSOR)):
            ffmpeg(
                "-i",
                self.source,
                "-map",
                "0:a:0",
                "-af",
                effect,
                "-ar",
                RATE,
                "-c:a",
                "pcm_f32le",
                dest,
            )
        original, fixed, dynamic = map(samples, (self.source, gained, compressed))
        self.assertAlmostEqual(contrast(original), contrast(fixed), places=3)
        self.assertLess(contrast(dynamic), contrast(original) - 3)
        self.assertEqual(len(dynamic), len(original))
        self.assertEqual(rms(dynamic, 7, 8), 0)
        self.assertTrue(all(math.isfinite(value) for value in dynamic))
        before = compressed.read_bytes()
        subprocess.run(
            ["ffmpeg", "-nostdin", "-n", "-i", str(self.source), str(compressed)],
            capture_output=True,
        )
        self.assertEqual(compressed.read_bytes(), before)
        print(
            f"\ncontrast: gain={contrast(fixed):.2f}, compressor={contrast(dynamic):.2f} dB"
        )

    def test_dual_mono_is_measured_before_normalization(self):
        stereo = self.root / "dual-mono.wav"
        ffmpeg(
            "-i",
            self.source,
            "-map",
            "0:a:0",
            "-af",
            "pan=stereo|c0=c0|c1=c0",
            "-ar",
            RATE,
            "-c:a",
            "pcm_f32le",
            stereo,
        )
        mono_i, stereo_i = (
            float(levels(path)["input_i"]) for path in (self.source, stereo)
        )
        self.assertAlmostEqual(stereo_i - mono_i, 3.01, delta=0.1)
        print(f"\nmono→dual-mono: {stereo_i - mono_i:.2f} LU")

    def test_diagnostics(self):
        for effect, expected in (
            ("ebur128=peak=true", "True peak:"),
            ("astats=metadata=0:reset=0", "RMS level dB"),
            ("silencedetect=noise=-40dB:d=0.15", "silence_start: 6"),
        ):
            log = ffmpeg(
                "-i",
                self.source,
                "-map",
                "0:a:0",
                "-af",
                effect,
                "-f",
                "null",
                "-",
            ).stderr.decode()
            self.assertIn(expected, log)
        ffmpeg(
            "-v",
            "error",
            "-xerror",
            "-i",
            self.source,
            "-map",
            "0:a:0",
            "-f",
            "null",
            "-",
        )

    def test_two_pass_normalization_and_final_mp4(self):
        master = self.root / "master.wav"
        delivery = self.root / "delivery.wav"
        ffmpeg(
            "-i",
            self.source,
            "-af",
            # First match the known 10x-louder section, then master dynamics.
            # Loudness normalization is not a substitute for this levelling.
            f"volume='if(between(t,3,6),0.1,1)':eval=frame,{COMPRESSOR},pan=stereo|c0=c0|c1=c0",
            "-ar",
            RATE,
            "-c:a",
            "pcm_f32le",
            master,
        )
        measured = levels(master)
        mapping = {
            "measured_I": "input_i",
            "measured_LRA": "input_lra",
            "measured_TP": "input_tp",
            "measured_thresh": "input_thresh",
            "offset": "target_offset",
        }
        self.assertTrue(
            all(math.isfinite(float(measured[key])) for key in mapping.values())
        )
        options = ":".join(f"{key}={measured[value]}" for key, value in mapping.items())
        result = ffmpeg(
            "-i",
            master,
            "-map",
            "0:a:0",
            "-af",
            f"loudnorm={TARGET}:{options}:linear=true:print_format=json",
            "-ar",
            RATE,
            "-c:a",
            "pcm_f32le",
            delivery,
        ).stderr.decode()
        applied = json.JSONDecoder().raw_decode(result[result.rindex("{") :])[0]
        self.assertIn(applied["normalization_type"], ("linear", "dynamic"))
        normalized = levels(delivery)
        self.assertAlmostEqual(float(normalized["input_i"]), -16, delta=0.5)
        self.assertLessEqual(float(normalized["input_tp"]), -1.4)
        picture, final = self.root / "picture.mp4", self.root / "final.mp4"
        ffmpeg(
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=320x180:r=30:d=12",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            picture,
        )
        ffmpeg(
            "-i",
            picture,
            "-i",
            delivery,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            RATE,
            "-movflags",
            "+faststart",
            final,
        )
        ffmpeg(
            "-v", "error", "-xerror", "-i", final, "-map", "0:a:0", "-f", "null", "-"
        )
        probe = json.loads(
            run(
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                final,
            ).stdout
        )
        audio = next(
            stream for stream in probe["streams"] if stream["codec_type"] == "audio"
        )
        self.assertEqual(
            (audio["codec_name"], audio["channels"], audio["sample_rate"]),
            ("aac", 2, "48000"),
        )
        self.assertAlmostEqual(float(audio["duration"]), 12, delta=0.1)
        final_levels = levels(final)
        self.assertAlmostEqual(float(final_levels["input_i"]), -16, delta=0.5)
        self.assertLessEqual(float(final_levels["input_tp"]), -1.0)
        print(
            f"\nmode={applied['normalization_type']}; final I={final_levels['input_i']} LUFS, TP={final_levels['input_tp']} dBTP"
        )

    def test_silent_file_is_not_a_normalization_target(self):
        silent = self.root / "silence.wav"
        ffmpeg(
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=mono",
            "-t",
            "4",
            "-c:a",
            "pcm_f32le",
            silent,
        )
        self.assertFalse(math.isfinite(float(levels(silent)["input_i"])))
        log = ffmpeg(
            "-i", silent, "-af", "silencedetect=noise=-40dB:d=0.15", "-f", "null", "-"
        ).stderr.decode()
        self.assertIn("silence_start: 0", log)


if __name__ == "__main__":
    unittest.main()
