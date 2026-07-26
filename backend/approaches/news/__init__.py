from __future__ import annotations

from typing import TYPE_CHECKING

from common.log import get_logger

from . import brief, sources
from .brief import CompanyNote, NewsBrief, empty_brief

if TYPE_CHECKING:
    from strategies.base import NewsSettings

log = get_logger("news")


def gather(settings: NewsSettings, tickers: list[str], news_doc: str = "") -> NewsBrief:
    """Fetch raw news via source adapters, then summarize into a NewsBrief.

    Returns a neutral empty brief if news is disabled or nothing is retrievable,
    so the caller can always proceed.
    """
    if not settings.enabled:
        log.info("News research disabled; skipping.")
        return empty_brief()
    if tickers:
        log.info("Gathering news for %d tickers: %s", len(tickers), ", ".join(tickers))
    else:
        log.info("Gathering macro/market/international news (no company tickers).")
    items = sources.gather_raw(settings, tickers)
    log.info("Fetched %d raw news item(s) from sources.", len(items))
    if not items:
        log.warning(
            "No news items retrieved (no network/API key, or sources unreachable); "
            "proceeding with neutral news context."
        )
    return brief.summarize(items, tickers, news_doc=news_doc)


__all__ = ["gather", "NewsBrief", "CompanyNote", "empty_brief", "brief", "sources"]
