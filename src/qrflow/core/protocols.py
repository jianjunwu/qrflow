# Copyright (c) 2026 QRFlow Authors
# License: MIT

"""Protocol definitions for pluggable components.

Defines structural interfaces using typing.Protocol so that components
can be swapped without inheritance coupling.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class EnhanceStep(Protocol):
    """A single image enhancement step.

    Each step receives an image and returns an enhanced version.
    The name attribute identifies the step for display and selection.
    """

    name: str
    label: str

    def process(self, image: np.ndarray) -> np.ndarray: ...


@runtime_checkable
class RecognizeBackend(Protocol):
    """A QR code recognition backend.

    Each backend attempts to decode a QR code from an image.
    Priority determines the order in which backends are tried.
    """

    name: str
    priority: int

    def recognize(self, image: np.ndarray) -> str | None: ...
