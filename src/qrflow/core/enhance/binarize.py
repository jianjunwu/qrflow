# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Adaptive binarization step."""

from __future__ import annotations

import cv2
import numpy as np

from qrflow.core.enhance.base import BaseEnhanceStep
from qrflow.core.enhance.registry import register


@register("binarize", "自适应二值化")
class BinarizeStep(BaseEnhanceStep):
    def process(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, blockSize=11, C=2,
        )

        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        chosen = adaptive if np.mean(adaptive) <= np.mean(otsu) else otsu
        return cv2.cvtColor(chosen, cv2.COLOR_GRAY2BGR)
