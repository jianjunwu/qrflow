# Copyright (c) 2026 QR Reconstructor Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env / CLI."""

    model_config = SettingsConfigDict(env_prefix="QRFLOW_", env_file=".env")

    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    upload_dir: str = "uploads"
    output_dir: str = "output"
    max_upload_mb: int = 16
    no_browser: bool = False

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir)
