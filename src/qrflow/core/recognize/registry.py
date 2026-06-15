# Copyright (c) 2026 QRFlow Authors
# License: Non-Commercial Use Only — see LICENSE file for full terms.

"""Registry for recognition backends.

Backends are auto-registered via the ``@register`` decorator at import time
and tried in priority-descending order.
"""

from __future__ import annotations

from qrflow.core.recognize.base import BaseRecognizeBackend

_registry: dict[str, BaseRecognizeBackend] = {}


def register(name: str, priority: int = 0):
    """Decorator that registers a recognition backend.

    Usage::

        @register("pyzbar", priority=10)
        class PyzbarBackend(BaseRecognizeBackend):
            ...
    """

    def decorator(cls: type[BaseRecognizeBackend]) -> type[BaseRecognizeBackend]:
        cls.name = name
        cls.priority = priority
        _registry[name] = cls()
        return cls

    return decorator


def get_backend(name: str) -> BaseRecognizeBackend:
    backend = _registry.get(name)
    if backend is None:
        raise KeyError(f"Recognition backend '{name}' not registered. Available: {list(_registry)}")
    return backend


def get_available_backends() -> list[BaseRecognizeBackend]:
    """Return instances of all registered backends, sorted by priority descending."""
    return sorted(_registry.values(), key=lambda b: b.priority, reverse=True)


def list_backends() -> list[str]:
    return list(_registry.keys())
