# Copyright (c) 2026 QRFlow Authors
# License: MIT

"""Upload route."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Request

from qrflow.core.models import UploadResponse

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS: set[str] = {"png", "jpg", "jpeg", "bmp", "gif", "webp", "tiff"}

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload(request: Request) -> UploadResponse:
    settings = request.app.state.settings
    form = await request.form()

    file = form.get("file")
    if file is None:
        return UploadResponse(success=False, error="未选择文件")

    filename: str = getattr(file, "filename", "")
    if not filename:
        return UploadResponse(success=False, error="文件名为空")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return UploadResponse(success=False, error="不支持的文件格式，请上传 PNG/JPG/BMP 等图片")

    unique_name = f"{uuid.uuid4().hex}.{ext}"

    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        return UploadResponse(success=False, error=f"文件超过 {settings.max_upload_mb}MB 限制")

    save_path = settings.upload_path / unique_name
    save_path.write_bytes(content)
    logger.info("Uploaded: %s", unique_name)

    return UploadResponse(success=True, filename=unique_name)
