# Copyright (c) 2026 QR Reconstructor Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""zxing-cpp recognition backend."""

from __future__ import annotations

import logging

import cv2
import numpy as np
from PIL import Image

from qrflow.core.recognize.base import BaseRecognizeBackend
from qrflow.core.recognize.registry import register

logger = logging.getLogger(__name__)


@register("zxing", priority=10)
class ZxingBackend(BaseRecognizeBackend):
    def __init__(self) -> None:
        self.available = True
        try:
            import zxing_cpp

            self._reader = zxing_cpp.BarcodeReader()
            self._zxing = zxing_cpp
        except Exception as exc:
            self.available = False
            logger.warning("zxing-cpp unavailable: %s", exc)

    def recognize(self, image: np.ndarray) -> str | None:
        if not self.available:
            return None
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            result = self._reader.read(
                pil_img.tobytes(), pil_img.width, pil_img.height,
                self._zxing.ImageFormat.RGB,
            )
        else:
            result = self._reader.read(
                image.tobytes(), image.shape[1], image.shape[0],
                self._zxing.ImageFormat.Lum,
            )
        return result.text if result and result.text else None
