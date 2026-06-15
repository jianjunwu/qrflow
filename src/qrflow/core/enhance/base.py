# Copyright (c) 2026 QRFlow Authors
# License: MIT

"""Base class for enhancement steps."""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod

import cv2
import numpy as np


class BaseEnhanceStep(ABC):
    """Abstract base for a single enhancement step.

    Subclasses must define `name`, `label`, and implement `process()`.
    """

    name: str
    label: str

    @abstractmethod
    def process(self, image: np.ndarray) -> np.ndarray: ...

    @staticmethod
    def encode_base64(image: np.ndarray) -> str:
        _, buffer = cv2.imencode(".png", image)
        b64 = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/png;base64,{b64}"
