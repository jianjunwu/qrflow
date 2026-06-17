"""CI helper: build minimal zbar from source or copy from system, place into _libs/.

Usage: python scripts/copy_zbar.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LIBS_DIR = Path("src/qrflow/_libs")
ZBAR_VERSION = "0.23.93"
ZBAR_URL = (
    "https://github.com/mchehab/zbar/archive"
    f"/refs/tags/{ZBAR_VERSION}.tar.gz"
)


def _build_zbar_linux() -> Path:
    """Download and build a minimal libzbar — no X11, video, dbus, or jpeg.

    Returns the path to the built libzbar.so.0.3.0.
    """
    work = Path(tempfile.mkdtemp(prefix="zbar-build-"))
    tarball = work / "zbar.tar.gz"
    print(f"Downloading zbar {ZBAR_VERSION} ...")
    subprocess.run(
        ["wget", "-q", ZBAR_URL, "-O", str(tarball)], check=True
    )
    subprocess.run(["tar", "xzf", str(tarball), "-C", str(work)], check=True)
    src_dir = work / f"zbar-{ZBAR_VERSION}"

    print("Configuring (minimal: no X11, video, dbus, jpeg) ...")
    subprocess.run(
        ["autoreconf", "-fi"], cwd=src_dir,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )
    subprocess.run(
        [
            "./configure",
            "--disable-video",
            "--without-x", "--without-xv",
            "--without-jpeg", "--without-imagemagick",
            "--without-python", "--without-gtk", "--without-qt",
            "--prefix=/usr",
        ],
        cwd=src_dir,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )

    print("Building ...")
    subprocess.run(
        ["make", "-j"], cwd=src_dir,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )

    # The built library
    result = list((src_dir / "zbar" / ".libs").glob("libzbar.so.*.*.*"))
    if not result:
        raise FileNotFoundError("Build succeeded but libzbar.so not found")
    return result[0]


def copy_zbar() -> None:
    # Clean any previous build artifacts.
    if LIBS_DIR.exists():
        for f in LIBS_DIR.glob("*"):
            f.unlink()
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
        raise FileNotFoundError(
            "libzbar.dylib not found. Install with: brew install zbar"
        )

    elif sys.platform == "linux":
        built = _build_zbar_linux()

        dest = LIBS_DIR / "libzbar.so.0"
        shutil.copy2(built, dest)
        print(f"Copied {built} -> {dest}")

        link = LIBS_DIR / "libzbar.so"
        if link.exists():
            link.unlink()
        link.symlink_to("libzbar.so.0")

        # Sanity check: the minimal build should only depend on libc.
        print("\nVerifying bundled libzbar deps (must be libc-only) ...")
        out = subprocess.check_output(
            ["ldd", str(dest)], text=True, stderr=subprocess.STDOUT,
        )
        missing = [l for l in out.splitlines() if "not found" in l]
        if missing:
            print("ERROR: missing deps:")
            for m in missing:
                print(f"  {m.strip()}")
            sys.exit(1)

        # Warn if anything beyond libc/ld-linux is pulled in.
        extra_deps = [
            l for l in out.splitlines()
            if "=>" in l
            and "libc.so" not in l
            and "libm.so" not in l
            and "libpthread" not in l
            and "ld-linux" not in l
        ]
        if extra_deps:
            print("WARNING: unexpected non-system deps:")
            for d in extra_deps:
                print(f"  {d.strip()}")

        print(f"OK — libzbar depends on libc only ({len(out.splitlines())} lines)")

    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


if __name__ == "__main__":
    copy_zbar()
