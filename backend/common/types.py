"""Shared TypedDict shapes for the dict payloads passed between modules.

These are static-typing-only constructs (a TypedDict is a plain dict at
runtime), used to document the data that flows across approach/strategy/db
boundaries without changing any runtime behavior.
"""

from datetime import datetime
from typing import NotRequired, Protocol, TypedDict


class PricePoint(TypedDict):
    date: str
    price: float
    volume: int
    openingPrice: float
    max: float
    min: float


class BookLevel(TypedDict):
    position: int
    price: float
    quantity: int


class Book(TypedDict):
    date: str
    bids: list[BookLevel]
    offers: list[BookLevel]


class Metrics(TypedDict):
    avg_daily_range_pct: float
    avg_volume: float
    spread_pct: float
    momentum_today_pct: float


class Candidate(TypedDict):
    ticker: str
    metrics: Metrics
    score: NotRequired[float]
    rank: NotRequired[int]


class NewsCompanyRow(TypedDict):
    ticker: str
    summary: str | None
    has_catalyst: bool


class LLMPick(TypedDict):
    ticker: str
    rank: int
    reason: str | None


class AggregatePick(TypedDict):
    ticker: str
    avg_rank: float
    times_first: int
    why: str | None
    final_rank: NotRequired[int]


class NewsItem(TypedDict):
    tier: str
    source: str
    title: str
    summary: str


class CompanyProfile(TypedDict, total=False):
    name: str
    adr: str | None


class PPIClient(Protocol):
    """Structural interface a real PPI client must satisfy to replace
    `common.ppi_client.MockPPIClient` (see CLAUDE.md)."""

    def search(
        self,
        ticker: str,
        date_from: datetime,
        date_to: datetime,
        lookback_days: int = ...,
    ) -> list[PricePoint]: ...

    def current(self, ticker: str) -> PricePoint: ...

    def book(self, ticker: str) -> Book: ...


class NewsBriefLike(Protocol):
    """Structural shape `common.db` needs from `approaches.news.brief.NewsBrief`,
    kept here (rather than importing that class) so `common/` stays independent
    of `approaches/`."""

    macro_summary: str
    market_summary: str
    international_summary: str
    market_risk_score: int
