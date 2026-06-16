"""API integration tests with FastAPI TestClient."""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image as PILImage
from fastapi.testclient import TestClient

from qrflow.api.lifespan import create_app
from qrflow.config.settings import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(
        upload_dir=str(tmp_path / "uploads"),
        output_dir=str(tmp_path / "output"),
    )


@pytest.fixture
def client(settings):
    app = create_app(settings)
    return TestClient(app)


@pytest.fixture
def uploaded_image(client):
    """Upload a simple test image and return its filename."""
    img = PILImage.new("RGB", (200, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    resp = client.post("/api/upload", files={"file": ("test.png", buf, "image/png")})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    return data["filename"]


class TestPages:
    def test_index_page(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_crop_button_visible_before_processing(self, client):
        """btnStartCrop 在文件已选中但尚未处理时应可见，不依赖 processed 状态."""
        resp = client.get("/")
        html = resp.text

        # 正确的逻辑：按钮仅在框选模式中隐藏
        assert "btnStartCrop.classList.toggle('hidden', cropState.active);" in html
        # bug 逻辑：按钮在处理前也会被隐藏 —— 不应存在
        assert "btnStartCrop.classList.toggle('hidden', cropState.active || !showCropHint)" not in html


class TestUpload:
    def test_no_file(self, client):
        resp = client.post("/api/upload")
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_valid_upload(self, client):
        img = PILImage.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        resp = client.post("/api/upload", files={"file": ("test.png", buf, "image/png")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["filename"].endswith(".png")


class TestDetect:
    def test_missing_filename(self, client):
        resp = client.post("/api/detect", json={})
        assert resp.status_code == 422

    def test_file_not_found(self, client):
        resp = client.post("/api/detect", json={"filename": "nonexistent.png"})
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_detect_valid(self, client, uploaded_image):
        resp = client.post("/api/detect", json={"filename": uploaded_image})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True


class TestProcess:
    def test_missing_filename(self, client):
        resp = client.post("/api/process", json={})
        assert resp.status_code == 422

    def test_file_not_found(self, client):
        resp = client.post("/api/process", json={"filename": "nonexistent.png"})
        assert resp.json()["success"] is False

    def test_process_valid(self, client, uploaded_image):
        resp = client.post("/api/process", json={"filename": uploaded_image})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "steps" in data
        assert "deduplicated" in data


class TestCrop:
    def test_file_not_found(self, client):
        resp = client.post("/api/manual_crop", json={
            "filename": "nonexistent.png",
            "x": 0, "y": 0, "width": 100, "height": 100,
        })
        assert resp.json()["success"] is False

    def test_crop_zero_dimensions(self, client, uploaded_image):
        """width 或 height 为 0 时应返回 422（模拟前端过早 cancelCropMode 的 bug）."""
        resp = client.post("/api/manual_crop", json={
            "filename": uploaded_image,
            "x": 0, "y": 0, "width": 0, "height": 0,
        })
        assert resp.status_code == 422

    def test_crop_valid(self, client, uploaded_image):
        resp = client.post("/api/manual_crop", json={
            "filename": uploaded_image,
            "x": 10, "y": 10, "width": 100, "height": 100,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "steps" in data

    def test_crop_multiple_regions_same_image(self, client, uploaded_image):
        """多区域框选：对同一图片多次调用 manual_crop 均应成功."""
        regions = [
            {"filename": uploaded_image, "x": 0, "y": 0, "width": 50, "height": 50},
            {"filename": uploaded_image, "x": 50, "y": 50, "width": 80, "height": 80},
            {"filename": uploaded_image, "x": 100, "y": 100, "width": 60, "height": 60},
        ]
        for i, body in enumerate(regions):
            resp = client.post("/api/manual_crop", json=body)
            assert resp.status_code == 200, f"region {i} failed with {resp.status_code}"
            data = resp.json()
            assert data["success"] is True, f"region {i}: {data}"

    def test_crop_missing_fields(self, client, uploaded_image):
        """缺少必填字段应返回 422."""
        resp = client.post("/api/manual_crop", json={"filename": uploaded_image})
        assert resp.status_code == 422

    def test_crop_negative_coords(self, client, uploaded_image):
        """负坐标应返回 422."""
        resp = client.post("/api/manual_crop", json={
            "filename": uploaded_image,
            "x": -1, "y": 0, "width": 100, "height": 100,
        })
        assert resp.status_code == 422
