# Copyright (c) 2026 QR Reconstructor Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Image encoding utilities."""

from __future__ import annotations

import base64

import cv2
import numpy as np


def encode_base64(image: np.ndarray) -> str:
    """Encode a numpy image array as a base64 PNG data URI."""
    _, buffer = cv2.imencode(".png", image)
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/png;base64,{b64}"
