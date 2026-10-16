"""Generate the specified local tone and publish the verified Manim insert."""

import math
from pathlib import Path
import shutil
import struct
import wave

root = Path(__file__).resolve().parents[1]
public = root / "public"
public.mkdir(exist_ok=True)
rate = 48000
count = 9600
samples = []
for i in range(count):
    envelope = min(1, i / 480, (count - 1 - i) / 480)
    samples.append(
        round(32767 * 0.1 * envelope * math.sin(2 * math.pi * 660 * i / rate))
    )
with wave.open(str(public / "tone.wav"), "wb") as out:
    out.setparams((1, 2, rate, count, "NONE", "not compressed"))
    out.writeframes(struct.pack(f"<{count}h", *samples))
shutil.copyfile(root / "renders/insert.mp4", public / "insert.mp4")
