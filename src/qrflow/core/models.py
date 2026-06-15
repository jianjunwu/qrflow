# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    success: bool
    filename: str | None = None
    error: str | None = None


class DetectRequest(BaseModel):
    filename: str


class DetectResponse(BaseModel):
    success: bool
    qr_regions: list[dict] = []
    original_image_base64: str | None = None
    error: str | None = None


class ProcessRequest(BaseModel):
    filename: str


class ProcessResponse(BaseModel):
    success: bool
    qr_regions: list[dict] | None = None
    original_image_base64: str | None = None
    steps: list[dict] | None = None
    deduplicated: list[dict] | None = None
    dedup_count: int = 0
    total_attempts: int = 0
    error: str | None = None


class CropRequest(BaseModel):
    filename: str
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
