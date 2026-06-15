"""Enhancement steps package.

Import all step modules to trigger ``@register`` decorators at import time.
"""

from qrflow.core.enhance.raw import RawStep
from qrflow.core.enhance.contrast import ContrastStep
from qrflow.core.enhance.denoise import DenoiseStep
from qrflow.core.enhance.binarize import BinarizeStep
from qrflow.core.enhance.morphology import MorphologyStep
from qrflow.core.enhance.perspective import PerspectiveStep
from qrflow.core.enhance.super_res import SuperResStep

__all__ = [
    "RawStep", "ContrastStep", "DenoiseStep", "BinarizeStep",
    "MorphologyStep", "PerspectiveStep", "SuperResStep",
]
