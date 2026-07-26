from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from approaches.base import ResearchApproach, register
from common import db
from common.log import get_logger
from common.types import NewsCompanyRow

from . import gather
from .brief import CompanyNote, NewsBrief

if TYPE_CHECKING:
    from strategies.base import Strategy

log = get_logger("news")

# Below this 0-100 trading-conditions score, warn that it's a poor day to trade.
RISK_WARN_THRESHOLD = 40


@register
class NewsApproach(ResearchApproach):
    name = "news"
    order = 2

    def run(self, strategy: Strategy, run_dt: datetime, **opts: Any) -> dict[str, Any]:
        det_run_id, picks = db.latest_deterministic_run_today(strategy.name)
        tickers = [p["ticker"] for p in picks]
        if det_run_id is None:
            log.info(
                "No deterministic run today — doing macro/market/international only."
            )

        settings = strategy.news_settings()
        brief = gather(settings, tickers, news_doc=strategy.news_doc() or "")

        notes = brief.company_notes_by_ticker()
        company_rows: list[NewsCompanyRow] = []
        for t in tickers:
            note = notes.get(t)
            company_rows.append(
                {
                    "ticker": t,
                    "summary": note.summary if note else None,
                    "has_catalyst": bool(note and note.has_catalyst_today),
                }
            )

        news_run_id = db.save_news_run(
            strategy.name, run_dt, det_run_id, brief, company_rows
        )
        _log_summary(brief, tickers, notes)
        if brief.market_risk_score < RISK_WARN_THRESHOLD:
            log.warning(
                "Trading-conditions score %d/100 — poor day; consider sitting out "
                "or trading small.",
                brief.market_risk_score,
            )

        log.info("News approach complete (run_id=%d).", news_run_id)
        return {"news_run_id": news_run_id, "brief": brief, "tickers": tickers}


def _log_summary(
    brief: NewsBrief, tickers: list[str], notes: dict[str, CompanyNote]
) -> None:
    lines = ["News analysis summary:"]
    lines.append(f"  Macro:  {brief.macro_summary or '(no data)'}")
    lines.append(f"  Market: {brief.market_summary or '(no data)'}")
    lines.append(f"  International: {brief.international_summary or '(no data)'}")
    lines.append(f"  Trading-conditions score: {brief.market_risk_score}/100 (50=neutral)")
    if tickers:
        lines.append("  Per-company:")
        for t in tickers:
            note = notes.get(t)
            if note:
                tag = " [CATALYST]" if note.has_catalyst_today else ""
                lines.append(f"    {t}: {note.summary}{tag}")
            else:
                lines.append(f"    {t}: (no news found)")
    else:
        lines.append("  Per-company: (no deterministic picks today)")
    log.info("\n".join(lines))
