"""Recreate public/tone.wav from the agreed signal specification."""

import math
import struct
import wave
from pathlib import Path

root = Path(__file__).resolve().parents[1]
rate = 48000
count = 9600
fade = 480
with wave.open(str(root / "public/tone.wav"), "wb") as wav:
    wav.setparams((1, 2, rate, count, "NONE", "not compressed"))
    wav.writeframes(
        b"".join(
            struct.pack(
                "<h",
                round(
                    32767
                    * 0.1
                    * min(1, i / fade, (count - 1 - i) / fade)
                    * math.sin(2 * math.pi * 660 * i / rate)
                ),
            )
            for i in range(count)
        )
    )
