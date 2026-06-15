# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Content deduplication logic."""

from __future__ import annotations


def deduplicate(contents: list[str]) -> list[str]:
    """Remove duplicate content entries, preserving first-occurrence order.

    Strips whitespace from each entry and filters empty strings.

    Args:
        contents: List of recognised content strings.

    Returns:
        Deduplicated list in first-seen order.
    """
    seen: set[str] = set()
    unique: list[str] = []
    for content in contents:
        stripped = content.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            unique.append(stripped)
    return unique


def build_deduplicated_results(step_results: list[dict]) -> list[dict]:
    """Build deduplicated result entries from pipeline step data.

    Each step_result dict should contain 'step_name' and a 'recognition'
    sub-dict with at least a 'content' key.

    Returns:
        List of entries, each with ``content``, ``source_steps``,
        and ``reconstructed_qr_base64``.
    """
    from qrflow.core.reconstruct.generator import reconstruct

    content_to_steps: dict[str, list[str]] = {}
    for step in step_results:
        recog = step.get("recognition", {})
        if recog.get("success") and recog.get("content"):
            content = recog["content"].strip()
            if content:
                content_to_steps.setdefault(content, []).append(
                    step.get("step_name", "unknown")
                )

    result: list[dict] = []
    seen: set[str] = set()
    for step in step_results:
        recog = step.get("recognition", {})
        content = (recog.get("content", "") or "").strip()
        if content and content not in seen:
            seen.add(content)
            result.append({
                "content": content,
                "source_steps": content_to_steps.get(content, []),
                "reconstructed_qr_base64": reconstruct(content),
            })

    return result
