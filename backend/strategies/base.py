from dataclasses import dataclass, field

from common.ppi_client import MockPPIClient, describe_source
from common.types import Candidate, CompanyProfile, PPIClient


@dataclass
class NewsSettings:
    enabled: bool = True
    top_n: int = 5
    macro_domains: list[str] = field(default_factory=list)
    market_domains: list[str] = field(default_factory=list)
    international_domains: list[str] = field(default_factory=list)
    company_official_domains: list[str] = field(default_factory=list)
    company_profiles: dict[str, CompanyProfile] = field(default_factory=dict)


class Strategy:
    name = "base"

    def watchlist(self) -> list[str]:
        raise NotImplementedError

    def market_client(self) -> PPIClient:
        """The market data source the deterministic stage reads from."""
        return MockPPIClient()

    def market_source(self) -> str:
        """Short description of that data source, for startup logging."""
        return describe_source("mock", True)

    def lookback_days(self) -> int:
        return 20

    def rank(self, candidates: list[Candidate]) -> list[Candidate]:
        """Screen + deterministically score candidates; return them ordered best-first."""
        raise NotImplementedError

    def final_count(self) -> int:
        return 5

    def llm_decision_runs(self) -> int:
        return 5

    def news_settings(self) -> NewsSettings:
        return NewsSettings(enabled=False)

    def financial_technical_doc(self) -> str:
        raise NotImplementedError

    def news_doc(self) -> str | None:
        return None


_REGISTRY: dict[str, type[Strategy]] = {}


def register(strategy_cls: type[Strategy]) -> type[Strategy]:
    _REGISTRY[strategy_cls.name] = strategy_cls
    return strategy_cls


def get_strategy(name: str) -> Strategy:
    if name not in _REGISTRY:
        raise KeyError(
            f"Unknown strategy '{name}'. Available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[name]()


def available() -> list[str]:
    return sorted(_REGISTRY)
