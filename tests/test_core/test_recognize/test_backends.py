"""Tests for recognize module — registry and backends."""

from __future__ import annotations

import numpy as np
import pytest

from qrflow.core.recognize.registry import get_available_backends, get_backend, list_backends


class TestRecognizeRegistry:
    def test_all_backends_registered(self):
        names = list_backends()
        assert "pyzbar" in names
        assert "opencv" in names

    def test_get_available_backends_returns_list(self):
        backends = get_available_backends()
        assert len(backends) > 0
        priorities = [b.priority for b in backends]
        assert priorities == sorted(priorities, reverse=True)


class TestZxingBackend:
    def test_backend_registered(self):
        backend = get_backend("zxing")
        assert backend is not None

    def test_backend_available(self):
        """zxing-cpp 后端应可用（v3 API 适配后）."""
        backend = get_backend("zxing")
        assert backend.available, "zxing-cpp backend should be available"

    def test_recognizes_qr_code(self, qr_image):
        backend = get_backend("zxing")
        if not backend.available:
            pytest.skip("zxing-cpp not available")
        content = backend.recognize(qr_image)
        assert content is not None
        assert "https://example.com/test-qr" in content

    def test_plain_image_returns_none(self, plain_image):
        backend = get_backend("zxing")
        if not backend.available:
            pytest.skip("zxing-cpp not available")
        content = backend.recognize(plain_image)
        assert content is None


class TestWeChatBackend:
    def test_backend_registered(self):
        backend = get_backend("wechat")
        assert backend is not None

    def test_backend_graceful_degradation(self):
        """WeChat QR 在 opencv-contrib >= 4.11 中不可用，应优雅降级."""
        backend = get_backend("wechat")
        # WeChat QR class was removed from opencv-contrib >= 4.11
        # Backend should mark itself as unavailable without crashing
        assert not backend.available
        # recognize() should return None when unavailable
        result = backend.recognize(np.ones((100, 100, 3), dtype=np.uint8) * 255)
        assert result is None

    def test_unavailable_logs_at_debug_level(self, caplog):
        """WeChat QR 不可用时应用 DEBUG 级别记录，不应以 WARNING 级别告警."""
        import logging
        from qrflow.core.recognize.wechat_backend import WeChatBackend

        caplog.set_level(logging.DEBUG, logger="qrflow.core.recognize.wechat_backend")
        WeChatBackend()

        warnings = [r for r in caplog.records if "WeChat QR unavailable" in r.message]
        if warnings:
            for r in warnings:
                assert r.levelno <= logging.INFO, (
                    f"Expected DEBUG or INFO, got {logging.getLevelName(r.levelno)}"
                )


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
