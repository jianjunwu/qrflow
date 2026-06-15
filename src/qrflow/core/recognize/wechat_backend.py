# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""WeChat QR (opencv-contrib) recognition backend."""

from __future__ import annotations

import logging

import numpy as np

from qrflow.core.recognize.base import BaseRecognizeBackend
from qrflow.core.recognize.registry import register

logger = logging.getLogger(__name__)


@register("wechat", priority=20)
class WeChatBackend(BaseRecognizeBackend):
    def __init__(self) -> None:
        self.available = True
        try:
            import cv2

            self._detector = cv2.wechat_qrcode_WeChatQRCode("", "", "", "")
        except Exception as exc:
            self.available = False
            logger.warning("WeChat QR unavailable: %s", exc)

    def recognize(self, image: np.ndarray) -> str | None:
        if not self.available:
            return None
        results, _ = self._detector.detectAndDecode(image)
        if results and len(results) > 0 and results[0]:
            return results[0]
        return None
