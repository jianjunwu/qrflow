# Copyright (c) 2026 QR Reconstructor Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Raw (identity) enhancement step."""

from __future__ import annotations

import numpy as np

from qrflow.core.enhance.base import BaseEnhanceStep
from qrflow.core.enhance.registry import register


@register("raw", "原始图片")
class RawStep(BaseEnhanceStep):
    def process(self, image: np.ndarray) -> np.ndarray:
        return image
