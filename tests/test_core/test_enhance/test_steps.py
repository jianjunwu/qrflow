"""Tests for enhance module — registry and steps."""

from __future__ import annotations

import numpy as np

from qrflow.core.enhance.registry import get_step, get_steps, list_steps


class TestEnhanceRegistry:
    def test_all_steps_registered(self):
        step_names = list_steps()
        expected = ["raw", "contrast", "denoise", "binarize", "morphology", "perspective", "super_res"]
        assert step_names == expected

    def test_get_step_returns_instance(self):
        step = get_step("raw")
        assert step.name == "raw"
        assert step.label == "原始图片"

    def test_get_step_unknown_raises(self):
        import pytest
        with pytest.raises(KeyError):
            get_step("nonexistent")


class TestEnhanceSteps:
    def test_raw_identity(self, test_image):
        step = get_step("raw")
        result = step.process(test_image)
        np.testing.assert_array_equal(result, test_image)

    def test_enhance_output_is_ndarray(self, test_image):
        for step in get_steps():
            result = step.process(test_image)
            assert isinstance(result, np.ndarray)

    def test_enhance_does_not_modify_input(self, test_image):
        original = test_image.copy()
        get_step("raw").process(original)
        np.testing.assert_array_equal(original, test_image)

    def test_base64_encode(self, test_image):
        from qrflow.core.enhance.base import BaseEnhanceStep
        encoded = BaseEnhanceStep.encode_base64(test_image)
        assert encoded.startswith("data:image/png;base64,")
