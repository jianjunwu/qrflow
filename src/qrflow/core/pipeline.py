# Copyright (c) 2026 QRFlow Authors
# License: MIT

"""Processing pipeline orchestrator for QR code reconstruction.

Binds together image enhancement, multi-scheme recognition, and
QR reconstruction into a single end-to-end flow.
"""

from __future__ import annotations

import logging
import os
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np

from qrflow.core.enhance.registry import get_steps
from qrflow.core.recognize.registry import get_available_backends
from qrflow.core.reconstruct.deduplicate import build_deduplicated_results
from qrflow.utils.bbox import merge_bboxes
from qrflow.utils.image import encode_base64

logger = logging.getLogger(__name__)

_MAX_CACHE_SIZE = 32


class Pipeline:
    """End-to-end QR code reconstruction pipeline."""

    def __init__(self) -> None:
        self._steps = get_steps()
        self._backends = get_available_backends()
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._cache_lock = threading.Lock()
        self._processing_locks: dict[str, threading.Lock] = {}
        self._processing_locks_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max(6, len(self._backends)))

    def _get_cache(self, image_path: str) -> dict | None:
        try:
            mtime = os.path.getmtime(image_path)
        except OSError:
            return None
        key = f"{image_path}:{mtime}"
        with self._cache_lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
        return None

    def _set_cache(self, image_path: str, result: dict) -> None:
        try:
            mtime = os.path.getmtime(image_path)
        except OSError:
            return
        key = f"{image_path}:{mtime}"
        with self._cache_lock:
            self._cache[key] = result
            self._cache.move_to_end(key)
            while len(self._cache) > _MAX_CACHE_SIZE:
                self._cache.popitem(last=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _get_or_create_processing_lock(self, image_path: str) -> threading.Lock:
        with self._processing_locks_lock:
            if image_path not in self._processing_locks:
                self._processing_locks[image_path] = threading.Lock()
            return self._processing_locks[image_path]

    def process(self, image_path: str) -> dict:
        cached = self._get_cache(image_path)
        if cached is not None:
            logger.info("Cache hit: %s", image_path)
            return cached

        proc_lock = self._get_or_create_processing_lock(image_path)
        with proc_lock:
            cached = self._get_cache(image_path)
            if cached is not None:
                logger.info("Cache hit (after lock): %s", image_path)
                return cached

            image: np.ndarray = cv2.imread(image_path)
            if image is None:
                raise FileNotFoundError(f"Cannot read image: {image_path}")

            original_base64 = encode_base64(image)
            qr_regions = self._locate_qr_codes(image)

            all_steps: list[dict] = []
            total_attempts = 0

            if qr_regions:
                for region_idx, region in enumerate(qr_regions):
                    crop = region["crop_array"]
                    region_decoded = False
                    for step in self._steps:
                        if region_decoded:
                            break
                        try:
                            enhanced = step.process(crop)
                        except Exception as exc:
                            logger.warning("Enhance step '%s' failed: %s", step.name, exc)
                            enhanced = crop
                        b64 = encode_base64(enhanced)
                        recog = self._recognize(enhanced)
                        if recog.get("success"):
                            region_decoded = True
                        step_name = f"区域{region_idx + 1}·{step.label}"
                        total_attempts += len(recog.get("all_results", []))
                        all_steps.append({
                            "step_key": step.name,
                            "step_name": step_name,
                            "image_base64": b64,
                            "recognition": recog,
                        })
                    del region["crop_array"]
            else:
                current = image
                global_decoded = False
                for step in self._steps:
                    if global_decoded:
                        break
                    try:
                        current = step.process(current)
                    except Exception as exc:
                        logger.warning("Enhance step '%s' failed: %s", step.name, exc)
                    b64 = encode_base64(current)
                    recog = self._recognize(current)
                    if recog.get("success"):
                        global_decoded = True
                    total_attempts += len(recog.get("all_results", []))
                    all_steps.append({
                        "step_key": step.name,
                        "step_name": step.label,
                        "image_base64": b64,
                        "recognition": recog,
                    })

            deduplicated = build_deduplicated_results(all_steps)

            logger.info(
                "Pipeline complete: %d region(s), %d step(s), %d unique result(s).",
                len(qr_regions), len(all_steps), len(deduplicated),
            )

            result = {
                "qr_regions": qr_regions,
                "original_image_base64": original_base64,
                "steps": all_steps,
                "deduplicated": deduplicated,
                "dedup_count": len(deduplicated),
                "total_attempts": total_attempts,
            }
            self._set_cache(image_path, result)
            return result

    def detect_regions(self, image_path: str) -> dict:
        image: np.ndarray = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")

        original_base64 = encode_base64(image)
        qr_regions = self._locate_qr_codes(image)

        for region in qr_regions:
            region.pop("crop_array", None)

        return {
            "qr_regions": qr_regions,
            "original_image_base64": original_base64,
        }

    def process_crop(self, crop_ndarray: np.ndarray) -> dict:
        original_base64 = encode_base64(crop_ndarray)
        all_steps: list[dict] = []
        total_attempts = 0

        current = crop_ndarray
        for step in self._steps:
            try:
                current = step.process(current)
            except Exception as exc:
                logger.warning("Enhance step '%s' failed: %s", step.name, exc)
            b64 = encode_base64(current)
            recog = self._recognize(current)
            total_attempts += len(recog.get("all_results", []))
            all_steps.append({
                "step_key": step.name,
                "step_name": step.label,
                "image_base64": b64,
                "recognition": recog,
            })

        deduplicated = build_deduplicated_results(all_steps)

        return {
            "qr_regions": [],
            "original_image_base64": original_base64,
            "steps": all_steps,
            "deduplicated": deduplicated,
            "dedup_count": len(deduplicated),
            "total_attempts": total_attempts,
        }

    # ------------------------------------------------------------------
    # Recognition
    # ------------------------------------------------------------------

    def _recognize(self, image: np.ndarray) -> dict:
        all_results: list[dict] = []
        first_content: str | None = None
        first_scheme: str | None = None
        backend_names = [b.name for b in self._backends]

        def _run(backend):
            try:
                content = backend.recognize(image)
            except Exception as exc:
                return {"scheme": backend.name, "success": False, "error": str(exc)}
            if content:
                return {"scheme": backend.name, "success": True, "content": content}
            return {"scheme": backend.name, "success": False, "error": "no QR code found"}

        futures = {self._executor.submit(_run, b): b for b in self._backends}
        for future in as_completed(futures):
            r = future.result()
            all_results.append(r)
            if r.get("success") and first_content is None:
                first_content = r["content"]
                first_scheme = r["scheme"]

        all_results.sort(key=lambda r: backend_names.index(r["scheme"]) if r["scheme"] in backend_names else 99)

        return {
            "success": first_content is not None,
            "content": first_content,
            "scheme": first_scheme,
            "all_results": all_results,
        }

    # ------------------------------------------------------------------
    # QR Code Localisation
    # ------------------------------------------------------------------

    def _locate_qr_codes(self, image: np.ndarray) -> list[dict]:
        all_bboxes: list[dict] = []
        h_img, w_img = image.shape[:2]

        # --- Pre-upsample for small images ---
        min_dim = min(w_img, h_img)
        if min_dim < 600:
            upscale = 4 if min_dim < 400 else 2
            logger.info("Pre-upsampling %dx%d image by %dx", w_img, h_img, upscale)
            up = cv2.resize(image, None, fx=upscale, fy=upscale, interpolation=cv2.INTER_LANCZOS4)
            up_gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY) if len(up.shape) == 3 else up

            try:
                from pyzbar.pyzbar import decode as _pzd
                for det in _pzd(up_gray):
                    if det.polygon and len(det.polygon) >= 4:
                        pts = np.array([(p.x / upscale, p.y / upscale) for p in det.polygon], dtype=np.int32)
                        x, y, w, h = int(np.min(pts[:, 0])), int(np.min(pts[:, 1])), int(np.max(pts[:, 0]) - np.min(pts[:, 0])), int(np.max(pts[:, 1]) - np.min(pts[:, 1]))
                        if w > 0 and h > 0:
                            all_bboxes.append({"bbox": (x, y, w, h), "source": f"pyzbar(pre-{upscale}x)"})
            except Exception as exc:
                logger.warning("Pre-upsample pyzbar failed: %s", exc)

            try:
                detector = cv2.QRCodeDetector()
                retval, points = detector.detect(up)
                if retval and points is not None:
                    pts = points if isinstance(points, np.ndarray) else np.array(points)
                    x, y, w, h = int(np.min(pts[:, 0]) / upscale), int(np.min(pts[:, 1]) / upscale), int((np.max(pts[:, 0]) - np.min(pts[:, 0])) / upscale), int((np.max(pts[:, 1]) - np.min(pts[:, 1])) / upscale)
                    if w > 0 and h > 0:
                        all_bboxes.append({"bbox": (x, y, w, h), "source": f"opencv(pre-{upscale}x)"})
            except Exception as exc:
                logger.warning("Pre-upsample OpenCV failed: %s", exc)

            if all_bboxes:
                merged = merge_bboxes(all_bboxes)
                return self._crop_regions(image, merged, h_img, w_img)

        all_bboxes = []

        # --- pyzbar on full image ---
        try:
            from pyzbar.pyzbar import decode as _pzd
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            for det in _pzd(gray):
                if det.polygon and len(det.polygon) >= 4:
                    pts = np.array([(p.x, p.y) for p in det.polygon], dtype=np.int32)
                    x, y = int(np.min(pts[:, 0])), int(np.min(pts[:, 1]))
                    w, h = int(np.max(pts[:, 0]) - x), int(np.max(pts[:, 1]) - y)
                    if w > 0 and h > 0:
                        all_bboxes.append({"bbox": (x, y, w, h), "source": "pyzbar"})
        except Exception as exc:
            logger.warning("pyzbar detection failed: %s", exc)

        # --- OpenCV on full image ---
        try:
            detector = cv2.QRCodeDetector()
            retval, points = detector.detect(image)
            if retval and points is not None:
                pts = points if isinstance(points, np.ndarray) else np.array(points)
                x, y = int(np.min(pts[:, 0])), int(np.min(pts[:, 1]))
                w, h = int(np.max(pts[:, 0]) - x), int(np.max(pts[:, 1]) - y)
                if w > 0 and h > 0:
                    all_bboxes.append({"bbox": (x, y, w, h), "source": "opencv"})
        except Exception as exc:
            logger.warning("OpenCV QR detection failed: %s", exc)

        # --- Multi-scale scanning ---
        if not all_bboxes:
            all_bboxes = self._scan_tiles(image, w_img, h_img)

        if not all_bboxes:
            logger.info("No QR code regions detected.")
            return []

        merged = merge_bboxes(all_bboxes)
        return self._crop_regions(image, merged, h_img, w_img)

    def _crop_regions(self, image: np.ndarray, bboxes: list[dict], h_img: int, w_img: int) -> list[dict]:
        regions: list[dict] = []
        for bbox_info in bboxes:
            x, y, w, h = bbox_info["bbox"]
            pad_x = int(w * 0.05)
            pad_y = int(h * 0.05)
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(w_img, x + w + pad_x)
            y2 = min(h_img, y + h + pad_y)
            crop = image[y1:y2, x1:x2].copy()
            regions.append({
                "bbox": (x1, y1, x2 - x1, y2 - y1),
                "crop_base64": encode_base64(crop),
                "crop_array": crop,
                "source": bbox_info["source"],
            })
        logger.info("Located %d QR code region(s).", len(regions))
        return regions

    # ------------------------------------------------------------------
    # Multi-scale scanning
    # ------------------------------------------------------------------

    def _scan_tiles(self, image: np.ndarray, img_w: int, img_h: int) -> list[dict]:
        try:
            from pyzbar.pyzbar import decode as _pzd
        except ImportError:
            logger.warning("pyzbar not available for multi-scale scan.")
            return []

        result: list[dict] = []
        seen: set[tuple] = set()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        scales = [1, 2, 3, 4, 5, 6]

        def _scan_at_scale(scale: int) -> list[dict]:
            local: list[dict] = []
            if scale == 1:
                s_img, s_gray = image, gray
            else:
                s_img = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                s_gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

            # pyzbar at this scale
            try:
                for det in _pzd(s_gray):
                    if det.polygon and len(det.polygon) >= 4:
                        pts = np.array([(p.x / scale, p.y / scale) for p in det.polygon], dtype=np.int32)
                        x, y = int(np.min(pts[:, 0])), int(np.min(pts[:, 1]))
                        w, h = int(np.max(pts[:, 0]) - x), int(np.max(pts[:, 1]) - y)
                        if w > 0 and h > 0:
                            local.append({"bbox": (x, y, w, h), "source": f"pyzbar({scale}x)"})
            except Exception:
                pass

            # OpenCV at this scale
            try:
                det = cv2.QRCodeDetector()
                ret, pts = det.detect(s_img)
                if ret and pts is not None:
                    pts_a = pts if isinstance(pts, np.ndarray) else np.array(pts)
                    x, y = int(np.min(pts_a[:, 0]) / scale), int(np.min(pts_a[:, 1]) / scale)
                    w, h = int((np.max(pts_a[:, 0]) - np.min(pts_a[:, 0])) / scale), int((np.max(pts_a[:, 1]) - np.min(pts_a[:, 1])) / scale)
                    if w > 5 and h > 5:
                        local.append({"bbox": (x, y, w, h), "source": f"opencv({scale}x)"})
            except Exception:
                pass

            # Sharpened detection for scales >= 5
            if scale >= 5:
                blur = cv2.GaussianBlur(s_gray, (0, 0), 1.5)
                sharp = cv2.addWeighted(s_gray, 2.0, blur, -1.0, 0)
                try:
                    for det in _pzd(sharp):
                        if det.polygon and len(det.polygon) >= 4:
                            pts = np.array([(p.x / scale, p.y / scale) for p in det.polygon], dtype=np.int32)
                            x, y = int(np.min(pts[:, 0])), int(np.min(pts[:, 1]))
                            w, h = int(np.max(pts[:, 0]) - x), int(np.max(pts[:, 1]) - y)
                            if w > 0 and h > 0:
                                local.append({"bbox": (x, y, w, h), "source": f"pyzbar({scale}x+sharp)"})
                except Exception:
                    pass

                try:
                    sharp_bgr = cv2.cvtColor(sharp, cv2.COLOR_GRAY2BGR)
                    ret, pts = det.detect(sharp_bgr)
                    if ret and pts is not None:
                        pts_a = pts if isinstance(pts, np.ndarray) else np.array(pts)
                        x, y = int(np.min(pts_a[:, 0]) / scale), int(np.min(pts_a[:, 1]) / scale)
                        w, h = int((np.max(pts_a[:, 0]) - np.min(pts_a[:, 0])) / scale), int((np.max(pts_a[:, 1]) - np.min(pts_a[:, 1])) / scale)
                        if w > 5 and h > 5:
                            local.append({"bbox": (x, y, w, h), "source": f"opencv({scale}x+sharp)"})
                except Exception:
                    pass

            return local

        futures = {self._executor.submit(_scan_at_scale, s): s for s in scales}
        for future in as_completed(futures):
            for item in future.result():
                key = item["bbox"]
                if key not in seen:
                    seen.add(key)
                    result.append(item)

        if result:
            logger.info("Multi-scale scan found %d QR region(s).", len(result))
        return result
