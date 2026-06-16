"""Patch pyzbar to load the bundled zbar shared library via explicit path.

This module MUST be imported before any pyzbar import.
It is loaded as the first import in qrflow/__init__.py.

On Linux, setting LD_LIBRARY_PATH via os.environ does NOT affect the current
process's dynamic linker — the linker reads it only at startup.  So we bypass
find_library() entirely and pre-load the bundled .so/.dylib with an explicit
path, then monkey-patch pyzbar.zbar_library.load() to return the cached handle.
"""
import ctypes
import sys
from pathlib import Path

_libs_dir = Path(__file__).resolve().parent / "_libs"

if not _libs_dir.exists() or not _libs_dir.is_dir():
    # No bundled libs — pyzbar will try to find the system libzbar.
    pass
else:
    if sys.platform == "darwin":
        _bundled = _libs_dir / "libzbar.dylib"
    elif sys.platform == "linux":
        # Pre-load transitive deps before libzbar.so.0 so the linker can
        # resolve them when libzbar loads.  Deps may themselves have deps,
        # so retry until all are loaded or no further progress is made.
        _pending = set()
        for _p in _libs_dir.glob("*.so*"):
            if _p.name in ("libzbar.so.0", "libzbar.so") or _p.is_symlink():
                continue
            _pending.add(_p)

        while _pending:
            _progress = False
            for _p in list(_pending):
                try:
                    ctypes.cdll.LoadLibrary(str(_p))
                    _pending.discard(_p)
                    _progress = True
                except OSError:
                    pass
            if not _progress:
                break  # remaining deps have unsatisfied transitive deps

        _bundled = _libs_dir / "libzbar.so.0"
    else:
        _bundled = None

    if _bundled and _bundled.exists():
        _libzbar = ctypes.cdll.LoadLibrary(str(_bundled))

        import pyzbar.zbar_library as _zbar_lib
        _zbar_lib.load = lambda: (_libzbar, [])
