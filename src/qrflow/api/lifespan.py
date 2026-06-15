# Copyright (c) 2026 QRFlow Authors
# License: MIT

"""FastAPI application factory with lifespan management."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from qrflow.config.settings import Settings
from qrflow.core.pipeline import Pipeline

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton pipeline
# ---------------------------------------------------------------------------
_pipeline: Pipeline | None = None


def get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.output_path.mkdir(parents=True, exist_ok=True)
    get_pipeline()
    logger.info("qrflow ready on %s:%d", settings.host, settings.port)
    yield


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title="qrflow",
        version="0.0.1",
        lifespan=lifespan,
    )

    app.state.settings = settings

    # Register routes
    from qrflow.api.routes import pages, upload, detect, process, crop

    app.include_router(pages.router)
    app.include_router(upload.router, prefix="/api")
    app.include_router(detect.router, prefix="/api")
    app.include_router(process.router, prefix="/api")
    app.include_router(crop.router, prefix="/api")

    # Static files
    _static_dir = Path(__file__).resolve().parent.parent.parent.parent / "static"
    if _static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

    # Ensure runtime directories exist
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.output_path.mkdir(parents=True, exist_ok=True)

    # Output files
    app.mount("/output", StaticFiles(directory=str(settings.output_path)), name="output")

    return app
