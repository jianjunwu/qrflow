# Copyright (c) 2026 QRFlow Authors
# License: MIT

"""Morphological operations: closing then opening."""

from __future__ import annotations

import cv2
import numpy as np

from qrflow.core.enhance.base import BaseEnhanceStep
from qrflow.core.enhance.registry import register


@register("morphology", "形态学操作")
class MorphologyStep(BaseEnhanceStep):
    def process(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)
        return cv2.cvtColor(opened, cv2.COLOR_GRAY2BGR)
