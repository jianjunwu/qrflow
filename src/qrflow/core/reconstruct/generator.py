# Copyright (c) 2026 QR Reconstructor Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""QR code image generation."""

from __future__ import annotations

import base64
import io

import qrcode
from PIL import Image as PILImage
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import SquareModuleDrawer

DEFAULT_SIZE: int = 300


def reconstruct(
    content: str,
    size: int = DEFAULT_SIZE,
    error_correction: int = qrcode.constants.ERROR_CORRECT_H,
) -> str:
    """Generate a clean QR code image for the given content.

    Args:
        content: The text or URL to encode.
        size: Target image dimension in pixels.
        error_correction: QR error correction level (default: H ~30%).

    Returns:
        A base64 PNG data URI string (``data:image/png;base64,...``).
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=error_correction,
        box_size=10,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=SquareModuleDrawer(),
        fill_color="black",
        back_color="white",
    )
    img = img.resize((size, size), resample=PILImage.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"
