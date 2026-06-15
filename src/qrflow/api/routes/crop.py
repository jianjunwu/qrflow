# Copyright (c) 2026 QR Reconstructor Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Manual crop route — process a user-selected region."""

from __future__ import annotations

import asyncio
import logging

import cv2
import numpy as np
from fastapi import APIRouter, Request

from qrflow.api.lifespan import get_pipeline
from qrflow.core.models import CropRequest, ProcessResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/manual_crop", response_model=ProcessResponse)
async def manual_crop(request: Request, body: CropRequest) -> ProcessResponse:
    settings = request.app.state.settings
    image_path = settings.upload_path / body.filename

    if not image_path.exists():
        return ProcessResponse(success=False, error="文件不存在或已过期，请重新上传")

    try:
        image = cv2.imread(str(image_path))
        if image is None:
            return ProcessResponse(success=False, error="图片读取失败")

        h_img, w_img = image.shape[:2]
        x = max(0, min(body.x, w_img - 1))
        y = max(0, min(body.y, h_img - 1))
        w = min(body.width, w_img - x)
        h = min(body.height, h_img - y)

        crop = image[y:y + h, x:x + w].copy()

        pipeline = get_pipeline()
        result = await asyncio.get_event_loop().run_in_executor(
            None, pipeline.process_crop, crop,
        )
        result["success"] = True
        logger.info("Manual crop: %dx%d, %d results.", w, h, result["dedup_count"])
        return ProcessResponse(**result)
    except Exception as exc:
        logger.exception("Manual crop error: %s", exc)
        return ProcessResponse(success=False, error=f"裁剪处理失败: {exc}")
