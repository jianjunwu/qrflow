# Copyright (c) 2026 QRFlow Authors
# License: MIT

"""zxing-cpp recognition backend."""

from __future__ import annotations

import logging

import numpy as np

from qrflow.core.recognize.base import BaseRecognizeBackend
from qrflow.core.recognize.registry import register

logger = logging.getLogger(__name__)


@register("zxing", priority=10)
class ZxingBackend(BaseRecognizeBackend):
    def __init__(self) -> None:
        self.available = True
        try:
            import zxingcpp  # noqa: F401

            self._zxing = zxingcpp
        except Exception as exc:
            self.available = False
            logger.warning("zxing-cpp unavailable: %s", exc)

    def recognize(self, image: np.ndarray) -> str | None:
        if not self.available:
            return None
        results = self._zxing.read_barcodes(image)
        if results and len(results) > 0:
            return results[0].text
        return None
