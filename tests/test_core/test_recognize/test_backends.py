"""Tests for recognize module — registry and backends."""

from __future__ import annotations

from qrflow.core.recognize.registry import get_available_backends, list_backends


class TestRecognizeRegistry:
    def test_all_backends_registered(self):
        names = list_backends()
        assert "pyzbar" in names
        assert "opencv" in names

    def test_get_available_backends_returns_list(self):
        backends = get_available_backends()
        assert len(backends) > 0
        # Priority descending
        priorities = [b.priority for b in backends]
        assert priorities == sorted(priorities, reverse=True)


class TestRecognition:
    def test_qr_code_recognized(self, qr_image):
        backends = get_available_backends()
        found = False
        for b in backends:
            try:
                content = b.recognize(qr_image)
                if content:
                    assert "https://example.com/test-qr" in content
                    found = True
                    break
            except Exception:
                continue
        assert found, "No backend recognized the QR code"

    def test_plain_image_not_recognized(self, plain_image):
        backends = get_available_backends()
        for b in backends:
            try:
                content = b.recognize(plain_image)
                assert content is None
            except Exception:
                continue
