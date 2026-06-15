# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Contrast enhancement via CLAHE."""

from __future__ import annotations

import cv2
import numpy as np

from qrflow.core.enhance.base import BaseEnhanceStep
from qrflow.core.enhance.registry import register


@register("contrast", "对比度增强")
class ContrastStep(BaseEnhanceStep):
    def process(self, image: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)
        lab = cv2.merge([l_channel, a_channel, b_channel])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
