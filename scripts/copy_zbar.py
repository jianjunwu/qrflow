"""CI helper: copy platform zbar library into _libs/ for bundling in the wheel.

Usage: python scripts/copy_zbar.py
"""
import shutil
import sys
from pathlib import Path

LIBS_DIR = Path("src/qrflow/_libs")


def copy_zbar() -> None:
    LIBS_DIR.mkdir(parents=True, exist_ok=True)

    if sys.platform == "darwin":
        for candidate in [
            "/opt/homebrew/lib/libzbar.dylib",
            "/usr/local/lib/libzbar.dylib",
        ]:
            src = Path(candidate)
            if src.exists():
                shutil.copy2(src, LIBS_DIR / "libzbar.dylib")
                print(f"Copied {src} -> {LIBS_DIR / 'libzbar.dylib'}")
                return
        raise FileNotFoundError("libzbar.dylib not found. Install with: brew install zbar")

    elif sys.platform == "linux":
        machine = __import__("platform").machine()
        candidates = [
            f"/usr/lib/{machine}-linux-gnu/libzbar.so.0",
            "/usr/lib/x86_64-linux-gnu/libzbar.so.0",
            "/usr/lib/aarch64-linux-gnu/libzbar.so.0",
            "/usr/lib/libzbar.so.0",
        ]
        for src in candidates:
            p = Path(src)
            if p.exists():
                dest = LIBS_DIR / "libzbar.so.0"
                shutil.copy2(p, dest)
                link = LIBS_DIR / "libzbar.so"
                if not link.exists():
                    link.symlink_to("libzbar.so.0")
                print(f"Copied {p} -> {dest}")
                return
        raise FileNotFoundError(
            "libzbar.so.0 not found. Install with: apt install libzbar0"
        )

    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


if __name__ == "__main__":
    copy_zbar()
