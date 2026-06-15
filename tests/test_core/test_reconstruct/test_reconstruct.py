"""Tests for reconstruct module."""

from __future__ import annotations

import base64
import io

from PIL import Image as PILImage

from qrflow.core.reconstruct.deduplicate import deduplicate, build_deduplicated_results
from qrflow.core.reconstruct.generator import reconstruct


class TestDeduplicate:
    def test_basic(self):
        assert deduplicate(["abc", "abc", "def", "abc"]) == ["abc", "def"]

    def test_strip_whitespace(self):
        assert deduplicate([" abc ", "abc"]) == ["abc"]

    def test_preserves_order(self):
        assert deduplicate(["c", "a", "b", "a", "c"]) == ["c", "a", "b"]

    def test_empty_input(self):
        assert deduplicate([]) == []

    def test_filters_empty_strings(self):
        assert deduplicate(["", "  ", "abc", ""]) == ["abc"]

    def test_all_duplicates(self):
        assert deduplicate(["x", "x", "x"]) == ["x"]

    def test_no_duplicates(self):
        assert deduplicate(["a", "b", "c"]) == ["a", "b", "c"]


class TestReconstruct:
    def test_returns_string(self):
        result = reconstruct("hello world")
        assert isinstance(result, str)

    def test_valid_data_uri(self):
        result = reconstruct("hello world")
        assert result.startswith("data:image/png;base64,")

    def test_decodable_png(self):
        result = reconstruct("hello world")
        b64_part = result.replace("data:image/png;base64,", "")
        png_bytes = base64.b64decode(b64_part)
        img = PILImage.open(io.BytesIO(png_bytes))
        assert img.format == "PNG"

    def test_different_sizes(self):
        r1 = reconstruct("test", size=100)
        r2 = reconstruct("test", size=400)
        b1 = base64.b64decode(r1.replace("data:image/png;base64,", ""))
        b2 = base64.b64decode(r2.replace("data:image/png;base64,", ""))
        assert PILImage.open(io.BytesIO(b1)).size == (100, 100)
        assert PILImage.open(io.BytesIO(b2)).size == (400, 400)


class TestBuildDeduplicatedResults:
    def test_empty_input(self):
        assert build_deduplicated_results([]) == []

    def test_single_content(self):
        steps = [{
            "step_name": "raw",
            "recognition": {"success": True, "content": "hello", "scheme": "pyzbar"},
        }]
        result = build_deduplicated_results(steps)
        assert len(result) == 1
        assert result[0]["content"] == "hello"
        assert "reconstructed_qr_base64" in result[0]
        assert result[0]["source_steps"] == ["raw"]

    def test_deduplicates_content(self):
        steps = [
            {"step_name": "raw", "recognition": {"success": True, "content": "same", "scheme": "pyzbar"}},
            {"step_name": "contrast", "recognition": {"success": True, "content": "same", "scheme": "opencv"}},
        ]
        result = build_deduplicated_results(steps)
        assert len(result) == 1
        assert result[0]["content"] == "same"
        assert "raw" in result[0]["source_steps"]
        assert "contrast" in result[0]["source_steps"]
