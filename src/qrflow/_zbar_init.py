"""Patch library search paths so pyzbar finds the bundled zbar shared library.

This module MUST be imported before any pyzbar import.
It is loaded as the first import in qrflow/__init__.py.
"""
import os
import sys
from pathlib import Path

_libs_dir = Path(__file__).resolve().parent / "_libs"
_lib_path = str(_libs_dir)

if _libs_dir.exists() and _libs_dir.is_dir():
    if sys.platform == "darwin":
        existing = os.environ.get("DYLD_LIBRARY_PATH", "")
        os.environ["DYLD_LIBRARY_PATH"] = f"{_lib_path}:{existing}" if existing else _lib_path
    elif sys.platform == "linux":
        existing = os.environ.get("LD_LIBRARY_PATH", "")
        os.environ["LD_LIBRARY_PATH"] = f"{_lib_path}:{existing}" if existing else _lib_path
    elif sys.platform == "win32":
        existing = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{_lib_path};{existing}" if existing else _lib_path
