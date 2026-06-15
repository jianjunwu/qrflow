# Copyright (c) 2026 QRFlow Authors
# License: MIT

"""Application entry point.

Bridges CLI arguments to Settings, creates the FastAPI app, and launches uvicorn.
"""

from __future__ import annotations

import logging
import os
import threading
import webbrowser

import uvicorn

from qrflow import __version__
from qrflow.api.lifespan import create_app
from qrflow.config.settings import Settings

logger = logging.getLogger(__name__)

BANNER = f"""=======================================================
  qrflow  v{__version__}
  作者 · jianjunwu  ·  github.com/jianjunwu/qrflow
  欢迎技术交流与指导
======================================================="""


def configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def run(**overrides) -> None:
    """Start the qrflow server.

    Accepts keyword arguments that override Settings defaults.
    Priority: CLI args > environment > .env > defaults.
    """

    # Merge overrides into Settings
    kwargs = {k: v for k, v in overrides.items() if v is not None}
    settings = Settings(**kwargs)

    configure_logging(settings.debug)

    print(BANNER)

    app = create_app(settings)

    # Auto-open browser (unless --no-browser or in debug mode)
    if not settings.no_browser:
        host_url = "127.0.0.1" if settings.host == "0.0.0.0" else settings.host
        url = f"http://{host_url}:{settings.port}"
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        logger.info("Opening browser at %s", url)

    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.output_dir, exist_ok=True)

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
