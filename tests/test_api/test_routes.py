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

    def test_crop_valid(self, client, uploaded_image):
        resp = client.post("/api/manual_crop", json={
            "filename": uploaded_image,
            "x": 10, "y": 10, "width": 100, "height": 100,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "steps" in data
