# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Perspective correction via finder-pattern detection."""

from __future__ import annotations

import logging
from typing import Tuple

import cv2
import numpy as np

from qrflow.core.enhance.base import BaseEnhanceStep
from qrflow.core.enhance.registry import register

logger = logging.getLogger(__name__)


@register("perspective", "透视矫正")
class PerspectiveStep(BaseEnhanceStep):
    def process(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        candidates: list[Tuple[float, cv2.typing.RotatedRect]] = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 50:
                continue
            rect = cv2.minAreaRect(cnt)
            (cx, cy), (w, h), angle = rect
            if w < 5 or h < 5:
                continue
            aspect_ratio = max(w, h) / (min(w, h) + 1e-6)
            if aspect_ratio > 2.0:
                continue
            candidates.append((area, rect))

        if len(candidates) < 3:
            logger.debug("Perspective correction: fewer than 3 finder patterns found; skipping.")
            return image

        candidates.sort(key=lambda x: x[0], reverse=True)
        top3_centers = np.array(
            [[r[0][0], r[0][1]] for _, r in candidates[:3]], dtype=np.float32
        )

        diffs = top3_centers[:, 0] - top3_centers[:, 1]
        sums = top3_centers[:, 0] + top3_centers[:, 1]
        tl_idx = int(np.argmin(sums))
        br_idx = int(np.argmax(sums))
        tr_idx = int(np.argmax(diffs))
        bl_idx = int(np.argmin(diffs))

        if tr_idx == bl_idx or tr_idx == tl_idx or bl_idx == tl_idx:
            remaining = [i for i in range(3) if i != tl_idx and i != br_idx]
            tr_idx = remaining[0] if remaining else tl_idx
            bl_idx = tr_idx

        src_pts = np.float32([
            top3_centers[tl_idx],
            top3_centers[tr_idx],
            top3_centers[bl_idx],
        ])

        v_tr = src_pts[1] - src_pts[0]
        v_bl = src_pts[2] - src_pts[0]
        br_est = src_pts[0] + v_tr + v_bl
        src_pts = np.float32([src_pts[0], src_pts[1], br_est, src_pts[2]])

        max_width = int(max(
            np.linalg.norm(src_pts[1] - src_pts[0]),
            np.linalg.norm(src_pts[2] - src_pts[3]),
        ))
        max_height = int(max(
            np.linalg.norm(src_pts[3] - src_pts[0]),
            np.linalg.norm(src_pts[2] - src_pts[1]),
        ))
        size = max(max_width, max_height, 300)

        dst_pts = np.float32([
            [0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1],
        ])

        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(
            image if len(image.shape) == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR),
            matrix, (size, size),
            borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255),
        )
        return warped
