from dataclasses import dataclass, field


@dataclass
class NewsSettings:
    enabled: bool = True
    top_n: int = 5
    macro_domains: list[str] = field(default_factory=list)
    market_domains: list[str] = field(default_factory=list)
    international_domains: list[str] = field(default_factory=list)
    company_official_domains: list[str] = field(default_factory=list)
    company_profiles: dict = field(default_factory=dict)


class Strategy:
    name = "base"

    def watchlist(self):
        raise NotImplementedError

    def lookback_days(self):
        return 20

    def rank(self, candidates):
        """Screen + deterministically score candidates; return them ordered best-first."""
        raise NotImplementedError

    def final_count(self):
        return 5

    def llm_decision_runs(self):
        return 5

    def news_settings(self):
        return NewsSettings(enabled=False)

    def financial_technical_doc(self):
        raise NotImplementedError

    def news_doc(self):
        return None


_REGISTRY = {}


def register(strategy_cls):
    _REGISTRY[strategy_cls.name] = strategy_cls
    return strategy_cls


def get_strategy(name):
    if name not in _REGISTRY:
        raise KeyError(
            f"Unknown strategy '{name}'. Available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[name]()


def available():
    return sorted(_REGISTRY)
