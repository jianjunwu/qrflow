# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Super-resolution step: Real-ESRGAN or OpenCV fallback."""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

from qrflow.core.enhance.base import BaseEnhanceStep
from qrflow.core.enhance.registry import register

logger = logging.getLogger(__name__)


@register("super_res", "超分辨率增强")
class SuperResStep(BaseEnhanceStep):
    def __init__(self) -> None:
        self._available: bool | None = None

    def process(self, image: np.ndarray) -> np.ndarray:
        if self._available is None:
            self._available = self._check_realesrgan()
        if self._available:
            return self._run_realesrgan(image)
        return self._fallback(image)

    @staticmethod
    def _check_realesrgan() -> bool:
        try:
            result = subprocess.run(
                ["realesrgan-ncnn-vulkan", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def _run_realesrgan(image: np.ndarray) -> np.ndarray:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fin, \
             tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fout:
            cv2.imwrite(fin.name, image)
            fin_path = fin.name
            fout_path = fout.name

        try:
            result = subprocess.run(
                ["realesrgan-ncnn-vulkan", "-i", fin_path, "-o", fout_path,
                 "-s", "2", "-n", "realesrgan-x4plus"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0 and Path(fout_path).exists():
                upscaled = cv2.imread(fout_path)
                if upscaled is not None:
                    return upscaled
            logger.warning("Real-ESRGAN failed: %s", result.stderr[:200])
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.warning("Real-ESRGAN error: %s", exc)
        finally:
            Path(fin_path).unlink(missing_ok=True)
            Path(fout_path).unlink(missing_ok=True)

        return SuperResStep._fallback(image)

    @staticmethod
    def _fallback(image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        upscaled = cv2.resize(image, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        blurred = cv2.GaussianBlur(upscaled, (0, 0), sigmaX=1.5)
        return cv2.addWeighted(upscaled, 1.5, blurred, -0.5, 0)
