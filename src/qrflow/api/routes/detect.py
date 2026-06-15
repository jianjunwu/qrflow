# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Detect route — locate QR regions without recognition."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Request

from qrflow.api.lifespan import get_pipeline
from qrflow.core.models import DetectRequest, DetectResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/detect", response_model=DetectResponse)
async def detect(request: Request, body: DetectRequest) -> DetectResponse:
    settings = request.app.state.settings
    image_path = settings.upload_path / body.filename

    if not image_path.exists():
        return DetectResponse(success=False, error="文件不存在或已过期，请重新上传")

    try:
        pipeline = get_pipeline()
        result = await asyncio.get_event_loop().run_in_executor(
            None, pipeline.detect_regions, str(image_path),
        )
        result["success"] = True
        return DetectResponse(**result)
    except FileNotFoundError as exc:
        logger.error("Image not found: %s", exc)
        return DetectResponse(success=False, error="图片文件读取失败")
    except Exception as exc:
        logger.exception("Detection error: %s", exc)
        return DetectResponse(success=False, error=f"检测失败: {exc}")
