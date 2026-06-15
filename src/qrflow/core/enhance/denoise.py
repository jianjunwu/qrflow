# Copyright (c) 2026 QRFlow Authors
# License: MIT

"""Denoising step: Gaussian blur + non-local means."""

from __future__ import annotations

import cv2
import numpy as np

from qrflow.core.enhance.base import BaseEnhanceStep
from qrflow.core.enhance.registry import register


@register("denoise", "去噪处理")
class DenoiseStep(BaseEnhanceStep):
    def process(self, image: np.ndarray) -> np.ndarray:
        blurred = cv2.GaussianBlur(image, (3, 3), 0)
        return cv2.fastNlMeansDenoisingColored(
            blurred, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21
        )
