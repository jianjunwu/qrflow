# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Bounding box utilities: IoU computation and union-find merging."""

from __future__ import annotations


def compute_iou(box1: tuple, box2: tuple) -> float:
    """Intersection over Union for two (x, y, w, h) boxes."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[0] + box1[2], box2[0] + box2[2])
    y2 = min(box1[1] + box1[3], box2[1] + box2[3])

    inter_w = max(0, x2 - x1)
    inter_h = max(0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = box1[2] * box1[3]
    area2 = box2[2] * box2[3]
    union_area = area1 + area2 - inter_area

    return inter_area / union_area if union_area > 0 else 0.0


def merge_bboxes(bboxes: list[dict]) -> list[dict]:
    """Merge overlapping bounding boxes using union-find (IoU > 0.3).

    Groups detections from multiple sources that refer to the same QR code
    and combines them into a single enclosing bounding box.
    """
    n = len(bboxes)
    if n <= 1:
        return bboxes

    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        root_i, root_j = find(i), find(j)
        if root_i != root_j:
            parent[root_j] = root_i

    for i in range(n):
        for j in range(i + 1, n):
            if compute_iou(bboxes[i]["bbox"], bboxes[j]["bbox"]) > 0.3:
                union(i, j)

    groups: dict[int, list[dict]] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(bboxes[i])

    merged: list[dict] = []
    for group in groups.values():
        min_x = min(b["bbox"][0] for b in group)
        min_y = min(b["bbox"][1] for b in group)
        max_x = max(b["bbox"][0] + b["bbox"][2] for b in group)
        max_y = max(b["bbox"][1] + b["bbox"][3] for b in group)

        sources = [b["source"] for b in group]
        if len(set(sources)) > 1:
            primary = "pyzbar+opencv"
        else:
            primary = sources[0]

        merged.append({
            "bbox": (min_x, min_y, max_x - min_x, max_y - min_y),
            "source": primary,
        })

    return merged
