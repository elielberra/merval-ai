from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel

from approaches.base import ResearchApproach, register
from common import db, llm
from common.log import get_logger

log = get_logger("decision")


class _RankedPick(BaseModel):
    ticker: str
    rank: int
    reason: str


class _Decision(BaseModel):
    picks: list[_RankedPick]


@register
class DecisionApproach(ResearchApproach):
    name = "decision"
    order = 3

    def run(self, strategy, run_dt, llm_runs=None, **opts):
        n = llm_runs or strategy.llm_decision_runs()

        det_run_id, picks = db.latest_deterministic_run_today(strategy.name)
        if det_run_id is None or not picks:
            log.info(
                "No deterministic picks today — nothing to decide. "
                "Run the deterministic approach first."
            )
            return {"decision_id": None}

        news_run_id, _fields, companies = db.latest_news_run_today(strategy.name)
        if news_run_id is None:
            log.info("No news run today — deciding on deterministic data only.")

        candidates, excluded = [], []
        for p in picks:
            if companies.get(p["ticker"], {}).get("has_catalyst"):
                excluded.append(p["ticker"])
            else:
                candidates.append(p)
        if excluded:
            log.info("Catalyst veto excluded: %s", ", ".join(excluded))
        if not candidates:
            log.info("All picks vetoed by news catalysts — nothing to decide.")
            return {"decision_id": None}

        system, user = _prompt(strategy, candidates, companies)
        model = llm.DECISION_MODEL
        log.info("Decision prompt — system:\n%s\n\nuser:\n%s", system, user)
        log.info("Running %d concurrent LLM decision call(s) with %s...", n, model)

        with ThreadPoolExecutor(max_workers=n) as executor:
            futures = [executor.submit(_one_call, system, user, model) for _ in range(n)]

        all_runs = []
        for i, future in enumerate(futures, start=1):
            run_picks = future.result()
            if not run_picks:
                log.warning("  run %d/%d produced no answer (skipped).", i, n)
                continue
            db.save_llm_run(
                strategy.name, run_dt, det_run_id, news_run_id, i, model, run_picks
            )
            all_runs.append(run_picks)
            order = " > ".join(
                p["ticker"] for p in sorted(run_picks, key=lambda x: x["rank"])
            )
            log.info("  run %d/%d: %s", i, n, order)

        if not all_runs:
            log.warning("No successful LLM runs (no API key or all failed).")
            return {"decision_id": None}

        aggregate = _aggregate(candidates, all_runs)
        decision_id = db.save_llm_decision(
            strategy.name, run_dt, det_run_id, news_run_id, len(all_runs), aggregate
        )
        _log_decision(aggregate, len(all_runs))
        log.info("Decision approach complete (decision_id=%d).", decision_id)
        return {"decision_id": decision_id, "aggregate": aggregate}


def _prompt(strategy, candidates, companies):
    lines = []
    for c in candidates:
        m = c["metrics"]
        note = companies.get(c["ticker"], {}).get("summary")
        news = f" | news: {note}" if note else ""
        lines.append(
            f"{c['ticker']}: avg daily range {m['avg_daily_range_pct']:.2f}%, "
            f"volume {m['avg_volume']:,.0f}, spread {m['spread_pct']:.2f}%, "
            f"today {m['momentum_today_pct']:+.2f}%{news}"
        )

    system = (
        "You are the final decision-maker for an intraday Merval stock-trading "
        "strategy. Using ONLY the strategy documents and the data provided, decide "
        "which of the candidate stocks are the best to BUY today for small, "
        "consistent intraday gains. Do not use outside knowledge or invent data.\n\n"
        "=== FINANCIAL-TECHNICAL APPROACH ===\n"
        + strategy.financial_technical_doc() + "\n\n"
        "=== NEWS APPROACH ===\n" + (strategy.news_doc() or "(none)")
    )
    user = (
        "Rank ALL of the candidate stocks below from best (rank 1) to worst for this "
        "strategy today. For each, give a SHORT reason (one clause, ~15 words max) "
        "grounded in its metrics and news. Every candidate must appear exactly once.\n\n"
        "Candidates:\n" + "\n".join(lines)
    )
    return system, user


def _one_call(system, user, model):
    try:
        response = llm.client().messages.parse(
            model=model,
            max_tokens=8192,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=_Decision,
        )
        parsed = response.parsed_output
        if parsed is None:
            log.warning("  (no parsed answer; stop_reason=%s)", response.stop_reason)
            return []
        return [
            {"ticker": p.ticker, "rank": p.rank, "reason": p.reason}
            for p in parsed.picks
        ]
    except Exception as exc:
        log.warning("LLM decision call failed: %s", exc)
        return []


def _aggregate(candidates, all_runs):
    tickers = [c["ticker"] for c in candidates]
    worst = len(tickers) + 1
    stats = {t: {"ranks": [], "times_first": 0, "best_rank": worst, "why": None} for t in tickers}

    for run in all_runs:
        by_ticker = {p["ticker"]: p for p in run}
        for t in tickers:
            p = by_ticker.get(t)
            rank = p["rank"] if p else worst
            stats[t]["ranks"].append(rank)
            if rank == 1:
                stats[t]["times_first"] += 1
            if p and rank < stats[t]["best_rank"]:
                stats[t]["best_rank"] = rank
                stats[t]["why"] = p.get("reason")

    agg = []
    for t in tickers:
        ranks = stats[t]["ranks"]
        avg = round(sum(ranks) / len(ranks), 2) if ranks else worst
        agg.append(
            {
                "ticker": t,
                "avg_rank": avg,
                "times_first": stats[t]["times_first"],
                "why": stats[t]["why"],
            }
        )
    agg.sort(key=lambda a: (a["avg_rank"], -a["times_first"]))
    for i, a in enumerate(agg, start=1):
        a["final_rank"] = i
    return agg


def _log_decision(aggregate, n):
    lines = [f"LLM decision — averaged over {n} run(s), best first:"]
    for a in aggregate:
        lines.append(
            f"  #{a['final_rank']} {a['ticker']}  "
            f"(avg rank {a['avg_rank']}, ranked #1 by {a['times_first']}/{n})"
        )
        if a.get("why"):
            lines.append(f"       why: {a['why']}")
    log.info("\n".join(lines))
