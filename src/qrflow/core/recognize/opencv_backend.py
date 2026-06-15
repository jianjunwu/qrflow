# Copyright (c) 2026 QR Reconstructor Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""OpenCV QRCodeDetector recognition backend."""

from __future__ import annotations

import logging

import cv2
import numpy as np

from qrflow.core.recognize.base import BaseRecognizeBackend
from qrflow.core.recognize.registry import register

logger = logging.getLogger(__name__)


@register("opencv", priority=30)
class OpenCVBackend(BaseRecognizeBackend):
    def __init__(self) -> None:
        self.available = True
        try:
            import cv2 as _cv2

            self._detector = _cv2.QRCodeDetector()
            self._detector.detectAndDecode  # warm-up
        except Exception as exc:
            self.available = False
            logger.warning("OpenCV QR unavailable: %s", exc)

    def recognize(self, image: np.ndarray) -> str | None:
        if not self.available:
            return None
        data, _, _ = self._detector.detectAndDecode(image)
        return data if data else None
