"""Shared pytest fixtures for QRFlow tests."""

from __future__ import annotations

import cv2
import numpy as np
import pytest
import qrcode
from PIL import Image as PILImage


@pytest.fixture(scope="session")
def test_image():
    """A simple synthetic image: white square with black border + noise."""
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (10, 10), (90, 90), (0, 0, 0), 2)
    img[50, 50] = [128, 128, 128]
    return img


@pytest.fixture(scope="session")
def qr_image():
    """A QR code image (BGR numpy array) encoding a test URL."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data("https://example.com/test-qr")
    qr.make(fit=True)
    pil_img = qr.make_image(fill_color="black", back_color="white")
    return cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)


@pytest.fixture(scope="session")
def plain_image():
    """A plain grey image with no QR code."""
    return np.ones((200, 200, 3), dtype=np.uint8) * 128
