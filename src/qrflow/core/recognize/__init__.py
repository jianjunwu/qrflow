"""Recognition backends package.

Import all backend modules to trigger ``@register`` decorators at import time.
"""

from qrflow.core.recognize.pyzbar_backend import PyzbarBackend
from qrflow.core.recognize.opencv_backend import OpenCVBackend
from qrflow.core.recognize.wechat_backend import WeChatBackend
from qrflow.core.recognize.zxing_backend import ZxingBackend

__all__ = ["PyzbarBackend", "OpenCVBackend", "WeChatBackend", "ZxingBackend"]
