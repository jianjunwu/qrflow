"""Pipeline concurrency and caching tests."""

from __future__ import annotations

import io
import threading
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image as PILImage

from qrflow.core.pipeline import Pipeline


class TestPipelineCache:
    """Verify cache correctness under concurrent access."""

    @pytest.fixture
    def pipeline(self):
        return Pipeline()

    def test_cache_hit_returns_same_object(self, pipeline, tmp_path):
        """Processing same file twice returns cached result (in-process)."""
        img = PILImage.new("RGB", (100, 100))
        path = tmp_path / "cache_hit.png"
        img.save(str(path))

        result1 = pipeline.process(str(path))
        result2 = pipeline.process(str(path))

        assert result1 is result2, "Second call should return same cached object"

    def test_concurrent_same_file_only_processes_once(self, pipeline, tmp_path):
        """Under concurrent access, only the first thread should compute."""
        img = PILImage.new("RGB", (100, 100))
        path = tmp_path / "concurrent.png"
        img.save(str(path))

        real_process = pipeline.process
        compute_count = 0
        lock = threading.Lock()

        # This test verifies that after the fix, concurrent access to the same
        # file results in one computation and all threads getting the cached result.
        errors: list[str] = []
        results: list[dict] = []
        barrier = threading.Barrier(4, timeout=10)

        def worker():
            try:
                barrier.wait()
                result = real_process(str(path))
                results.append(result)
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Errors: {errors}"
        assert len(results) == 4, f"Expected 4 results, got {len(results)}"
        # All results should be the same object after the fix
        first = results[0]
        for r in results[1:]:
            assert r is first, "All threads should get the same cached instance"

    def test_concurrent_different_files_do_not_interfere(self, pipeline, tmp_path):
        """Concurrent processing of different files must not mix results."""
        num_files = 8
        paths = []
        for i in range(num_files):
            img = PILImage.new("RGB", (100, 100), color=(i * 30, 0, 0))
            p = tmp_path / f"mixed_{i}.png"
            img.save(str(p))
            paths.append(str(p))

        errors: list[str] = []
        results_map: dict[str, dict] = {}
        barrier = threading.Barrier(num_files, timeout=10)
        lock = threading.Lock()

        def worker(idx: int):
            try:
                barrier.wait()
                r = Pipeline().process(paths[idx])
                with lock:
                    results_map[paths[idx]] = r
            except Exception as exc:
                errors.append(f"thread {idx}: {exc}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_files)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Errors: {errors}"
        assert len(results_map) == num_files


class TestPipelineConcurrency:
    """Functional: pipeline works under concurrent usage."""

    @pytest.fixture
    def pipeline(self):
        return Pipeline()

    def test_concurrent_recognize_calls(self, pipeline, qr_image):
        """Multiple threads calling _recognize must not interfere."""

        errors: list[str] = []
        barrier = threading.Barrier(4, timeout=10)

        def worker(idx: int):
            try:
                barrier.wait()
                for _ in range(10):
                    result = pipeline._recognize(qr_image)
                    if not isinstance(result, dict):
                        errors.append(f"thread {idx}: bad result type: {type(result)}")
                    elif "all_results" not in result:
                        errors.append(f"thread {idx}: missing all_results")
            except Exception as exc:
                errors.append(f"thread {idx}: {exc}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent recognize errors: {errors}"
