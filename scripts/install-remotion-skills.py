#!/usr/bin/env python3
"""Install the pinned, self-contained upstream skill without engine packages."""

import argparse
import io
from pathlib import Path, PurePosixPath
import tarfile
from urllib.request import urlopen


REVISION = "1441a11e95db35443bd76bb318386c0d3ca00053"
URL = f"https://codeload.github.com/remotion-dev/skills/tar.gz/{REVISION}"
SKILL = "remotion-best-practices"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Target Git workspace (defaults to the OMR source workspace)",
    )
    workspace = parser.parse_args().workspace.resolve()
    if not workspace.is_dir() or not (workspace / ".git").exists():
        parser.error("Target must be an existing Git workspace")
    destination = workspace / ".opencode" / "skills" / SKILL
    # Refuse symlinked destinations and parents to preserve unrelated user files.
    for parent in (destination, *destination.parents):
        if parent == workspace:
            break
        if parent.is_symlink():
            parser.error(f"Refusing symlinked destination: {parent}")

    with urlopen(URL, timeout=60) as response:
        archive = response.read()
    prefix = f"skills-{REVISION}/skills/{SKILL}/"
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not member.name.startswith(prefix):
                continue
            relative = PurePosixPath(member.name[len(prefix) :])
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError(f"Unsafe archive path: {member.name}")
            if member.isdir():
                continue
            if not member.isfile():
                raise RuntimeError(f"Unsupported archive member: {member.name}")
            source = tar.extractfile(member)
            if source is None:
                raise RuntimeError(f"Unreadable archive member: {member.name}")
            with source:
                files[Path(*relative.parts)] = source.read()
    if Path("SKILL.md") not in files:
        raise RuntimeError("Archive does not contain the expected skill")

    if destination.exists():
        actual = {
            p.relative_to(destination) for p in destination.rglob("*") if p.is_file()
        }
        if (
            any(p.is_symlink() for p in destination.rglob("*"))
            or actual != set(files)
            or any((destination / p).read_bytes() != data for p, data in files.items())
        ):
            parser.error(
                f"Existing dependency differs; preserve/review it manually: {destination}"
            )
        print(f"Already installed, contents verified: {destination} @ {REVISION}")
        return

    for relative, data in files.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(
        f"Installed {len(files)} unchanged upstream files: {destination} @ {REVISION}"
    )


if __name__ == "__main__":
    main()
