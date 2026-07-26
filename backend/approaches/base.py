from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from strategies.base import Strategy


class ResearchApproach:
    name = "base"
    order = 0

    def run(self, strategy: Strategy, run_dt: datetime, **opts: Any) -> dict[str, Any]:
        """Do the approach's work for a strategy, persist results, return a summary."""
        raise NotImplementedError


_REGISTRY: dict[str, type[ResearchApproach]] = {}


def register(cls: type[ResearchApproach]) -> type[ResearchApproach]:
    _REGISTRY[cls.name] = cls
    return cls


def get_approach(name: str) -> ResearchApproach:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown approach '{name}'. Available: {names()}")
    return _REGISTRY[name]()


def ordered() -> list[ResearchApproach]:
    return [cls() for cls in sorted(_REGISTRY.values(), key=lambda c: c.order)]


def names() -> list[str]:
    return [c.name for c in sorted(_REGISTRY.values(), key=lambda c: c.order)]
