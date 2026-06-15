"""Rewrite wheel tag to py3-none-{platform_tag}.

Usage: python scripts/rewrite_tag.py <platform_tag>

Example:
  python scripts/rewrite_tag.py macosx_11_0_arm64
  python scripts/rewrite_tag.py manylinux_2_17_x86_64
  python scripts/rewrite_tag.py win_amd64

Finds all .whl files in dist/, rewrites their WHEEL metadata tag
and renames the file accordingly.
"""
import os
import sys
from pathlib import Path
from zipfile import ZipFile


def rewrite(wheel_path: Path, platform_tag: str) -> Path | None:
    temp = wheel_path.with_suffix(".whl.tmp")

    old_tag: str | None = None
    new_tag = f"py3-none-{platform_tag}"

    with ZipFile(wheel_path, "r") as zin, ZipFile(temp, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith("/WHEEL"):
                content = data.decode("utf-8")
                new_lines = []
                for line in content.split("\n"):
                    if line.startswith("Tag:"):
                        old_tag = line.split(":", 1)[1].strip()
                        new_lines.append(f"Tag: {new_tag}")
                    else:
                        new_lines.append(line)
                content = "\n".join(new_lines)
                zout.writestr(item, content.encode("utf-8"))
            else:
                zout.writestr(item, data)

    wheel_path.unlink()
    temp.rename(wheel_path)

    if old_tag:
        new_name = wheel_path.name.replace(old_tag, new_tag)
        new_path = wheel_path.parent / new_name
        os.rename(wheel_path, new_path)
        return new_path
    return wheel_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/rewrite_tag.py <platform_tag>")
        print("  e.g. macosx_11_0_arm64, manylinux_2_17_x86_64, win_amd64")
        sys.exit(1)

    platform_tag = sys.argv[1]
    for f in Path("dist").glob("*.whl"):
        result = rewrite(f, platform_tag)
        if result:
            print(f"  {f.name} -> {result.name}")
