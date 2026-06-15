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
        for candidate in [
            "/usr/lib/x86_64-linux-gnu/libzbar.so.0",
            "/usr/lib/libzbar.so.0",
        ]:
            src = Path(candidate)
            if src.exists():
                shutil.copy2(src, LIBS_DIR / "libzbar.so.0")
                (LIBS_DIR / "libzbar.so").symlink_to("libzbar.so.0")
                print(f"Copied {src} -> {LIBS_DIR / 'libzbar.so.0'}")
                return
        raise FileNotFoundError(
            "libzbar.so.0 not found. Install with: apt install libzbar0"
        )

    elif sys.platform == "win32":
        import urllib.request
        import zipfile
        import tempfile

        url = (
            "https://github.com/NaturalHistoryMuseum/zbar-windows"
            "/releases/download/v0.10/zbar-0.10-windows-x86_64.zip"
        )
        with tempfile.TemporaryDirectory() as tmp:
            zp = Path(tmp) / "zbar.zip"
            print(f"Downloading {url} ...")
            urllib.request.urlretrieve(url, zp)
            with zipfile.ZipFile(zp, "r") as zf:
                for name in zf.namelist():
                    if name.lower().endswith(".dll"):
                        zf.extract(name, tmp)
                        print(f"Extracted {name}")
            for dll in Path(tmp).rglob("*.dll"):
                dest = LIBS_DIR / dll.name
                shutil.copy2(dll, dest)
                print(f"Copied {dll.name} -> {dest}")


if __name__ == "__main__":
    copy_zbar()
