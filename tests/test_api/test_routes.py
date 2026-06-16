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

    def test_crop_rects_persist_across_file_switch(self, client):
        """切换文件时框选状态应保存到旧 record 并从新 record 恢复."""
        resp = client.get("/")
        html = resp.text

        # selectFile 应保存旧文件的框选区间
        assert "oldFile.cropRects = [...cropState.rects]" in html
        # selectFile 应从新文件恢复框选区间
        assert "cropState.rects = [...newFile.cropRects]" in html
        # startCropMode 不应重置 rects 为 []（cancelCropMode 中允许有）
        start_crop = html.index('function startCropMode()')
        end = html.index('cropState.startX', start_crop)
        assert 'cropState.rects = []' not in html[start_crop:end]

    def test_record_has_crop_rects_field(self, client):
        """新创建的 record 应包含 cropRects 字段."""
        resp = client.get("/")
        html = resp.text
        assert "cropRects" in html

    def test_start_crop_mode_preserves_restored_rects(self, client):
        """startCropMode 恢复已有 rects 后不应被后续代码清掉."""
        resp = client.get("/")
        html = resp.text

        # 截取 startCropMode 函数体
        start = html.index('function startCropMode()')
        end = html.index('function cancelCropMode()')
        body = html[start:end]

        # btnConfirmCrop 的 remove('hidden') 必须在 add('hidden') 之后
        # （否则先 show 再 hide，rects 的 confirm 按钮就被藏回去了）
        add_pos = body.index("btnConfirmCrop.classList.add('hidden')")
        remove_pos = body.index("btnConfirmCrop.classList.remove('hidden')")
        assert remove_pos > add_pos, \
            "btnConfirmCrop 应先 add('hidden') 再按需 remove('hidden')，而非相反"

        # clearAllCropOverlays 之后若 rects 存在应调用 renderAllCropOverlays
        assert 'renderAllCropOverlays()' in body, \
            "startCropMode 应在有已保存 rects 时重新渲染 overlay"

    def test_cancel_crop_mode_does_not_save_to_wrong_file(self, client):
        """cancelCropMode 不应把旧文件 rects 存到新文件的 record 上（串图）."""
        resp = client.get("/")
        html = resp.text

        # 截取 cancelCropMode 函数体
        start = html.index('function cancelCropMode()')
        end = html.index('function confirmCrop()')
        body = html[start:end]

        # save 逻辑应在 selectFile 中完成，cancelCropMode 里不应再有
        assert 'cropRects = [...cropState.rects]' not in body, \
            "cancelCropMode 不应保存 rects（会串图）"

    def test_render_all_crop_overlays_converts_orig_to_display(self, client):
        """renderAllCropOverlays 应将原图坐标换算为当前显示坐标（防止位移）."""
        resp = client.get("/")
        html = resp.text

        # 截取 renderAllCropOverlays 函数体
        start = html.index('function renderAllCropOverlays()')
        # 下一函数是 onCropMouseDown
        end = html.index('function onCropMouseDown(')
        body = html[start:end]

        # 应有获取当前图像显示尺寸的逻辑
        assert 'getBoundingClientRect' in body, \
            "renderAllCropOverlays 应获取当前图像显示尺寸以换算坐标"
        # 应有利用 orig 坐标换算显示坐标的逻辑
        assert 'origX' in body and 'origY' in body, \
            "renderAllCropOverlays 应通过 origX/origY 反向计算显示坐标"

    def test_crop_zoomed_has_no_max_height_transition(self, client):
        """进入/退出 crop 模式时 max-height 不应有过渡动画，防止 overlay 定位偏移."""
        resp = client.get("/static/style.css")
        css = resp.text

        # .preview-image 基础规则不应有 max-height 过渡
        idx = css.index('.preview-image {')
        end = css.index('.preview-image.crop-zoomed')
        base_block = css[idx:end]

        assert 'transition: max-height' not in base_block, \
            ".preview-image 不应有 max-height transition，退出框选时的动画会导致 getBoundingClientRect 尺寸不准"

    def test_selectfile_restores_confirmed_crop_ui(self, client):
        """selectFile 恢复框选时应同时恢复确认后的 UI 状态."""
        resp = client.get("/")
        html = resp.text

        start = html.index('function selectFile(')
        end = html.index('function startCropMode()')
        body = html[start:end]

        # 恢复时显示"处理选中区域"按钮
        assert 'btnManualProcess.classList.remove' in body, \
            "selectFile 恢复框选时应显示 btnManualProcess"
        # 恢复时隐藏"开始处理"按钮
        assert "btnProcess.classList.add('hidden')" in body, \
            "selectFile 恢复框选时应隐藏 btnProcess（用处理选中区域代替）"

    def test_processall_uses_manual_crop_for_files_with_rects(self, client):
        """有框选的文件走 /api/manual_crop，无框选走 /api/process."""
        resp = client.get("/")
        html = resp.text

        # 截取 startProcessingAll 函数体
        start = html.index('async function startProcessingAll()')
        end = html.index('function abortProcessing()')
        body = html[start:end]

        assert 'record.cropRects' in body, \
            "startProcessingAll 应检查 record 的 cropRects 字段"
        assert 'manual_crop' in body, \
            "startProcessingAll 对有框选文件应调用 /api/manual_crop"


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
