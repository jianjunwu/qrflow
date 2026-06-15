# Copyright (c) 2026 QR Reconstructor Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""pyzbar (zbar) recognition backend."""

from __future__ import annotations

import logging

import cv2
import numpy as np

from qrflow.core.recognize.base import BaseRecognizeBackend
from qrflow.core.recognize.registry import register

logger = logging.getLogger(__name__)


@register("pyzbar", priority=40)
class PyzbarBackend(BaseRecognizeBackend):
    def __init__(self) -> None:
        self.available = True
        try:
            from pyzbar.pyzbar import decode as _decode

            self._decode = _decode
        except Exception as exc:
            self.available = False
            logger.warning("pyzbar unavailable: %s", exc)

    def recognize(self, image: np.ndarray) -> str | None:
        if not self.available:
            return None
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        results = self._decode(gray)
        if results:
            return results[0].data.decode("utf-8", errors="replace")
        return None
