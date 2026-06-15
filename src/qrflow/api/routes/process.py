# Copyright (c) 2026 QR Reconstructor Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Process route — full reconstruction pipeline."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Request

from qrflow.api.lifespan import get_pipeline
from qrflow.core.models import ProcessRequest, ProcessResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/process", response_model=ProcessResponse)
async def process_image(request: Request, body: ProcessRequest) -> ProcessResponse:
    settings = request.app.state.settings
    image_path = settings.upload_path / body.filename

    if not image_path.exists():
        return ProcessResponse(success=False, error="文件不存在或已过期，请重新上传")

    try:
        pipeline = get_pipeline()
        result = await asyncio.get_event_loop().run_in_executor(
            None, pipeline.process, str(image_path),
        )
        result["success"] = True
        logger.info("Pipeline: %d results from %d attempts.", result["dedup_count"], result["total_attempts"])
        return ProcessResponse(**result)
    except FileNotFoundError as exc:
        logger.error("Image not found: %s", exc)
        return ProcessResponse(success=False, error="图片文件读取失败")
    except Exception as exc:
        logger.exception("Pipeline error: %s", exc)
        return ProcessResponse(success=False, error=f"处理失败: {exc}")
