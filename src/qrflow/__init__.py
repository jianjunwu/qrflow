"""QRFlow — QR code reconstruction toolkit."""

from qrflow._zbar_init import *  # noqa: F401,F403 — must be before any pyzbar import
from importlib.metadata import version

__version__ = version("qrflow")
