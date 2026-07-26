from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from approaches.base import ResearchApproach, register
from common import db
from common.log import get_logger
from common.metrics import compute_metrics
from common.ppi_client import MockPPIClient
from common.types import Candidate, PPIClient

if TYPE_CHECKING:
    from strategies.base import Strategy

log = get_logger("deterministic")


@register
class DeterministicApproach(ResearchApproach):
    name = "deterministic"
    order = 1

    def run(
        self,
        strategy: Strategy,
        run_dt: datetime,
        client: PPIClient | None = None,
        **opts: Any,
    ) -> dict[str, Any]:
        client = client or MockPPIClient()
        date_from = run_dt - timedelta(days=30)

        log.info("Deterministic screen over %d tickers...", len(strategy.watchlist()))
        candidates: list[Candidate] = []
        for ticker in strategy.watchlist():
            history = client.search(
                ticker, date_from, run_dt, lookback_days=strategy.lookback_days()
            )
            current = client.current(ticker)
            book = client.book(ticker)
            candidates.append(
                {"ticker": ticker, "metrics": compute_metrics(history, current, book)}
            )

        ranked = strategy.rank(candidates)
        picks = ranked[: strategy.final_count()]
        for rank, c in enumerate(picks, start=1):
            c["rank"] = rank

        run_id = db.save_deterministic_run(strategy.name, run_dt, picks)
        log.info(
            "Deterministic picks (top %d): %s",
            len(picks),
            ", ".join(f"{c['ticker']}({c['score']:.1f})" for c in picks) or "(none)",
        )
        log.info("Deterministic approach complete (run_id=%d).", run_id)
        return {"run_id": run_id, "picks": picks}
