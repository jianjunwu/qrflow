"""CI helper: copy platform zbar library and its transitive deps into _libs/.

Usage: python scripts/copy_zbar.py
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

LIBS_DIR = Path("src/qrflow/_libs")

# Libs guaranteed present on any Linux system — no need to bundle.
_SYSTEM_LIBS = {
    "linux-vdso.so.1",
    "libc.so.6",
    "libm.so.6",
    "libpthread.so.0",
    "libdl.so.2",
    "librt.so.1",
    "libresolv.so.2",
    "libstdc++.so.6",
    "libgcc_s.so.1",
    "libcrypt.so.1",
    "libutil.so.1",
}

# Sonames that contain "ld-linux" (dynamic linker) — never bundle.
_IS_LD_LINUX = re.compile(r"ld-linux")


def _ldd(lib_path: Path) -> list[Path]:
    """Run ldd on *lib_path* and return a list of resolved dependency paths."""
    out = subprocess.check_output(["ldd", str(lib_path)], text=True)
    deps = []
    for line in out.splitlines():
        # Two forms:
        #   libfoo.so.N => /usr/lib/libfoo.so.N (0x...)
        #   /lib64/ld-linux-x86-64.so.2 (0x...)   (no soname, absolute path)
        if "=>" in line:
            # "soname => path (addr)"
            right = line.rsplit("=>", 1)[1]
            path_str = right.split("(")[0].strip()
        else:
            # Try to extract an absolute path
            parts = line.strip().split()
            # First token should be an absolute path
            if parts and parts[0].startswith("/"):
                path_str = parts[0]
            else:
                continue

        p = Path(path_str)
        if p.exists() and p.name not in _SYSTEM_LIBS and not _IS_LD_LINUX.search(p.name):
            deps.append(p)
    return deps


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
        src = None
        for c in candidates:
            p = Path(c)
            if p.exists():
                src = p
                break
        if src is None:
            raise FileNotFoundError(
                "libzbar.so.0 not found. Install with: apt install libzbar0"
            )

        dest = LIBS_DIR / "libzbar.so.0"
        shutil.copy2(src, dest)
        print(f"Copied {src} -> {dest}")

        link = LIBS_DIR / "libzbar.so"
        if not link.exists():
            link.symlink_to("libzbar.so.0")

        # ── copy transitive deps ──────────────────────────────────────────
        for dep in _ldd(src):
            dep_dest = LIBS_DIR / dep.name
            if dep_dest.exists():
                continue
            shutil.copy2(dep, dep_dest)
            print(f"Copied dep {dep} -> {dep_dest}")

    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


if __name__ == "__main__":
    copy_zbar()
