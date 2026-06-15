"""CLI tests with Typer CliRunner."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from qrflow.cli import app

runner = CliRunner()


class TestCLI:
    def test_serve_help(self):
        result = runner.invoke(app, ["serve", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.stdout
        assert "--port" in result.stdout
        assert "--debug" in result.stdout
        assert "--no-browser" in result.stdout
