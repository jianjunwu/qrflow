# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""CLI entry point for qrflow."""

from __future__ import annotations

import webbrowser
from typing import Annotated

import typer

app = typer.Typer()


@app.command()
def serve(
    host: Annotated[str, typer.Option("--host", "-h", help="绑定地址")] = "0.0.0.0",
    port: Annotated[int, typer.Option("--port", "-p", help="端口")] = 8080,
    debug: Annotated[bool, typer.Option("--debug", help="调试模式")] = False,
    upload_dir: Annotated[str, typer.Option("--upload-dir", help="上传目录")] = "uploads",
    output_dir: Annotated[str, typer.Option("--output-dir", help="输出目录")] = "output",
    max_upload_mb: Annotated[int, typer.Option("--max-upload-mb", help="最大上传(MB)")] = 16,
    no_browser: Annotated[bool, typer.Option("--no-browser", help="不自动打开浏览器")] = False,
):
    """启动 qrflow 服务"""
    from qrflow.main import run

    run(
        host=host,
        port=port,
        debug=debug,
        upload_dir=upload_dir,
        output_dir=output_dir,
        max_upload_mb=max_upload_mb,
        no_browser=no_browser,
    )
