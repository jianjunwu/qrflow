# Copyright (c) 2026 QR Reconstructor Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Base class for recognition backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class BaseRecognizeBackend(ABC):
    """Abstract base for a QR code recognition backend.

    Subclasses must define `name`, `priority`, and implement `recognize()`.
    """

    name: str
    priority: int = 0

    @abstractmethod
    def recognize(self, image: np.ndarray) -> str | None: ...
