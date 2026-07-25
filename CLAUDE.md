# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

`frontend/` (React + TypeScript via Vite) renders a dashboard from hardcoded dummy data. `backend/` (Python) has the analysis phase of the trading agent: it scans a watchlist, ranks the top 3 stocks for a "small, consistent daily gains" strategy, and stores the results in SQLite. Neither talks to the real PPI API yet — the user's PPI account isn't activated, so both use mock data shaped like the real API responses.

## Purpose

merval-ai is being built as an AI agent for operating on the Merval (Argentine) stock exchange. The intended integration point is the Portfolio Personal Inversiones (PPI) API, which offers account/portfolio queries, instrument lookup and historical values, real-time quotes, and sending/cancelling buy/sell orders (via a Python library or REST). PPI provides a Sandbox environment for testing before hitting production data.

Reference docs for the PPI API live in `ppi-official-api-docs/docs/` (a separately cloned, nested git repo). Use this path when looking up PPI request/response shapes (e.g. `ppi-official-api-docs/docs/api/documentacionRest.md`, `documentacionPython.md`). That directory is git-ignored here since it's external reference material, not part of this codebase — read it locally for API details, but don't expect it to be tracked or committed.

## Frontend

`frontend/` is a Vite + React + TypeScript app, styled with plain CSS (no UI framework). Commands (run from `frontend/`): `npm install`, `npm run dev`, `npm run build`.

The dashboard (`src/components/Dashboard.tsx`, `src/components/StockCard.tsx`) shows today's positions from `src/data/dummyStocks.ts`, shaped to match the PPI REST API's instrument/position fields so it's a drop-in swap once the backend exists. Gain/loss is shown via a magnitude-banded green/red badge (see `src/index.css` for the band thresholds) — update `dummyStocks.ts` and the `Stock` type in `src/types.ts` together if the data shape changes. "Sell Now" / "Create Sell Order" buttons are currently inert placeholders (no backend to call yet).

### Color palette (light theme — keep this discrete, light-blue look)

Light theme only (no dark mode). The chrome is discrete light blue; red/green is reserved for the gain/loss delta so semantics stay unambiguous. Tokens are CSS custom properties in `src/index.css`:

| Role | Token | Value |
|------|-------|-------|
| Page background | `--page` | `#eef4fb` |
| Card surface | `--surface-1` | `#ffffff` |
| Accent (ticker, buttons) | `--accent` | `#2a78d6` |
| Accent soft (button hover) | `--accent-soft` | `#dcebfb` |
| Primary text | `--text-primary` | `#12263a` |
| Secondary text | `--text-secondary` | `#52627a` |
| Muted (labels) | `--muted` | `#8a97a8` |
| Border (hairline) | `--border` | `#d5e3f2` |
| Gain (delta ↑) | `--gain` | `#006300` |
| Loss (delta ↓) | `--loss` | `#d03b3b` |

## Backend / Research agent

`backend/` is plain Python (venv + `requirements.txt`, no framework). Commands (run from `backend/`):

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your key in .env
python run_research.py                       # runs all approaches in order
python run_research.py --research technical  # or just one: technical | news | decision
python run_research.py --research decision --llm-runs 5   # override the ensemble size
```

`ANTHROPIC_API_KEY` is loaded from `backend/.env` (via `python-dotenv`); `.env.example` is the committed template, `.env` is gitignored — never commit the real key. `--strategy small-daily-gains` is the default. Every run writes a timestamped log (with per-approach analysis summaries) to `backend/logs/research.log`.

### Three layers: `common/` (infra) · `approaches/` (research approaches) · `strategies/` (per-strategy)

```
backend/
  common/            shared, strategy-agnostic infra: ppi_client, metrics, llm, db, log
  approaches/        the research approaches — modular siblings, run in order
    base.py          ResearchApproach interface + ordered registry
    technical/       (order 1) deterministic: data → metrics → rank → store  (NO Claude)
    news/            (order 2) read today's technical picks → news → store  (sources.py + brief.py)
    decision/        (order 3) LLM ensemble → store each call + averaged aggregate
  strategies/
    base.py          Strategy interface + registry
    small_daily_gains/  strategy.py, config.py, research/{technical,news}-approach.md
  run_research.py    CLI: --research {technical,news,decision,all}, --strategy, --llm-runs
```

**Two independent axes:** *strategy* (what rules to use) and *research approach* (which stage to run). Add a strategy → a folder under `strategies/`; add an approach → a folder under `approaches/` implementing `ResearchApproach` (`name`, `order`, `run(strategy, run_dt)`) and `@register`ed. Neither touches shared code.

### The three approaches (run in order; each independently runnable, hands off via the DB)
1. **Technical** (`approaches/technical/`) — **deterministic, no Claude, runs with no API key.** Gathers market data, computes the three pillars (volatility=`avg_daily_range_pct`, liquidity=`avg_volume`+`spread_pct`, momentum=`momentum_today_pct`), screens (`MIN_DAILY_RANGE_PCT`) and scores 0–100, stores the **top 5** picks (`FINAL_COUNT`) with a full timestamp.
2. **News** (`approaches/news/`) — reads **today's latest technical run** from the DB and researches **only those tickers** (macro/market/international always; company search skipped if there are no picks). `sources.py` prefers RSS / known URLs, falls back to a scoped Claude web-search; `brief.py` summarizes into a `NewsBrief` (macro/market/international + per-company catalyst flags). **Fetched web content is untrusted** — the summarizer never follows instructions embedded in a page. It's a **safety-veto layer**, never a re-ranker.
3. **Decision** (`approaches/decision/`) — the **final "which stocks to buy" call**, run as an **ensemble** (`--llm-runs`, default `LLM_DECISION_RUNS = 5`). Applies the catalyst veto, then makes N independent Claude calls each ranking the candidates with a short reason. **Every call is stored individually** so answers can be compared; the aggregate is a deterministic **average rank** (+ times-ranked-#1) giving an ordered recommendation and a consistency read.

### Design invariants
- **Deterministic technical rank; Claude judges at the decision stage; news only vetoes/warns.** Technical order is reproducible; the decision ensemble surfaces the LLM's judgment *and* its consistency across runs; news can exclude a catalyst stock or flag a risk-off day but never reorders.
- **Models:** news = `claude-sonnet-5`; decision = `claude-sonnet-5` (`DECISION_MODEL` in `common/llm.py`) — it's an N-call ensemble, so Sonnet by default; switch to Opus for max quality on the money decision.
- Scores are **heuristic suitability (0–100), not calibrated probabilities.** `~0.85%` round-trip cost is an estimate — re-verify against the real PPI tier.
- **Swapping in the real PPI API:** write a class with the same `.current`/`.search`/`.book` interface as `MockPPIClient` and pass it to the technical approach's `run(strategy, run_dt, client=...)`.
- **DB** (`data/merval_research.db`, gitignored) stores each stage separately with a full `analysis_datetime`: `technical_runs`/`technical_picks`, `news_runs`/`news_company`, `llm_runs`/`llm_run_picks` (individual calls) + `llm_decisions`/`llm_decision_picks` (aggregate). News & decision feed from the **latest technical run of the current day**.

**Pre-existing trading skills** (research-only, none Merval/PPI-specific — optional future references, not used): `agiprolabs/claude-trading-skills`, `zubair-trabzada/ai-trading-claude`, `tradermonty/claude-trading-skills`, `OctagonAI/skills`. Prefer the repo's own strategy files over pulling third-party trading code (supply-chain risk; none target this market).

## Commit conventions

Use Conventional Commits for all commit messages in this repo (e.g. `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).

Keep commit messages short, concrete, and easy to understand — a single plain-language line describing what changed, no multi-paragraph bodies unless truly necessary. Do not add a Claude/AI co-author line.
