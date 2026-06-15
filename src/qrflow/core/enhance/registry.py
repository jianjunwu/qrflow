# Copyright (c) 2026 QRFlow Authors
# License: MIT

"""Registry for enhancement steps.

Steps are auto-registered via the ``@register`` decorator at import time.
"""
from __future__ import annotations

from qrflow.core.enhance.base import BaseEnhanceStep

_registry: dict[str, type[BaseEnhanceStep]] = {}


def register(name: str, label: str):
    """Decorator that registers an enhancement step class.

    Usage::

        @register("contrast", "对比度增强")
        class ContrastStep(BaseEnhanceStep):
            ...
    """

    def decorator(cls: type[BaseEnhanceStep]) -> type[BaseEnhanceStep]:
        cls.name = name
        cls.label = label
        _registry[name] = cls
        return cls

    return decorator


def get_step(name: str) -> BaseEnhanceStep:
    """Instantiate a single step by name."""
    cls = _registry.get(name)
    if cls is None:
        raise KeyError(f"Enhancement step '{name}' not registered. Available: {list(_registry)}")
    return cls()


def get_steps(names: list[str] | None = None) -> list[BaseEnhanceStep]:
    """Return step instances for the given names.

    If ``names`` is None, returns all registered steps in registration order.
    """
    if names is None:
        names = list(_registry.keys())
    return [get_step(n) for n in names]


def list_steps() -> list[str]:
    """Return all registered step names in order."""
    return list(_registry.keys())
