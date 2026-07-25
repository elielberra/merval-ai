class ResearchApproach:
    name = "base"
    order = 0

    def run(self, strategy, run_dt, **opts):
        """Do the approach's work for a strategy, persist results, return a summary."""
        raise NotImplementedError


_REGISTRY = {}


def register(cls):
    _REGISTRY[cls.name] = cls
    return cls


def get_approach(name):
    if name not in _REGISTRY:
        raise KeyError(f"Unknown approach '{name}'. Available: {names()}")
    return _REGISTRY[name]()


def ordered():
    return [cls() for cls in sorted(_REGISTRY.values(), key=lambda c: c.order)]


def names():
    return [c.name for c in sorted(_REGISTRY.values(), key=lambda c: c.order)]
