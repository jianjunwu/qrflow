"""Tests for utils module."""

from __future__ import annotations

from qrflow.utils.bbox import compute_iou, merge_bboxes
from qrflow.utils.image import encode_base64


class TestImageUtils:
    def test_encode_base64(self, test_image):
        encoded = encode_base64(test_image)
        assert encoded.startswith("data:image/png;base64,")


class TestBboxUtils:
    def test_iou_identical(self):
        box = (0, 0, 100, 100)
        assert compute_iou(box, box) == 1.0

    def test_iou_disjoint(self):
        assert compute_iou((0, 0, 10, 10), (100, 100, 10, 10)) == 0.0

    def test_merge_single(self):
        bboxes = [{"bbox": (0, 0, 100, 100), "source": "pyzbar"}]
        result = merge_bboxes(bboxes)
        assert len(result) == 1
        assert result[0]["bbox"] == (0, 0, 100, 100)

    def test_merge_overlapping(self):
        bboxes = [
            {"bbox": (0, 0, 100, 100), "source": "pyzbar"},
            {"bbox": (20, 20, 100, 100), "source": "opencv"},
        ]
        result = merge_bboxes(bboxes)
        assert len(result) == 1
        assert "pyzbar+opencv" in result[0]["source"]
