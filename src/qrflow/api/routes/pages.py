# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Frontend page routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

_INDEX_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "templates" / "index.html"


@router.get("/")
async def index():
    return FileResponse(_INDEX_PATH)
