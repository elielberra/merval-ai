# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

`frontend/` (React + TypeScript via Vite) renders a dashboard from hardcoded dummy data. `backend/` (Python) has the analysis phase of the trading agent: it scans a watchlist, ranks the top 3 stocks for a "small, consistent daily gains" strategy, and stores the results in SQLite. Neither talks to the real PPI API yet — the user's PPI account isn't activated, so both use mock data shaped like the real API responses. The backend's real-PPI path *is* written and only needs credentials plus a config flag to switch on (see the design invariants below).

## Purpose

merval-ai is being built as an AI agent for operating on the Merval (Argentine) stock exchange. The intended integration point is the Portfolio Personal Inversiones (PPI) API, which offers account/portfolio queries, instrument lookup and historical values, real-time quotes, and sending/cancelling buy/sell orders (via a Python library or REST). PPI provides a Sandbox environment for testing before hitting production data.

Reference docs for the PPI API live in `ppi-official-api-docs/docs/` (a separately cloned, nested git repo). Use this path when looking up PPI request/response shapes (e.g. `ppi-official-api-docs/docs/api/documentacionRest.md`, `documentacionPython.md`). That directory is git-ignored here since it's external reference material, not part of this codebase — read it locally for API details, but don't expect it to be tracked or committed.

## Frontend

`frontend/` is a Vite + React + TypeScript app, plain CSS (no UI framework). Commands (from `frontend/`): `npm install`, `npm run dev`, `npm run build`.

**Running the full app locally:** two processes — the backend API (`cd backend && source .venv/bin/activate && uvicorn api:app --port 8000`) and the frontend (`cd frontend && npm run dev`). Vite proxies `/api` → `localhost:8000` (`vite.config.ts`), so the app calls `/api/...` same-origin (no CORS).

**Tabs** (`src/App.tsx`): a fixed top nav bar switches between two tabs.
- **Research** (`src/components/research/`) — reads real results from the API. `ResearchTab.tsx` has a date picker (default today, `max=today`); if today has no data it shows a **Run analysis** button that POSTs `/api/research/run` and polls `/api/research/status` (spinner ~2 min) then reloads. With data it renders top-to-bottom: `MarketRiskGauge` (0–100 trading-conditions score, colored), `TopPicks` (the decision aggregate in order — metrics + why + "#1 in X/N" agreement — with a collapsed toggle revealing the individual LLM analyses via `IndividualAnalyses`), and `NewsSummary`. API client + types in `src/research/api.ts`.
- **Positions** (`src/components/Dashboard.tsx`, `StockCard.tsx`) — the original screen, **unchanged**: today's positions from `src/data/dummyStocks.ts` with a magnitude-banded green/red gain/loss badge and inert Sell buttons.

### Color palette (light theme — keep this discrete, light-blue look)

Light theme only (no dark mode). The chrome is discrete light blue. Two distinct color conventions:
- **Two-color gain/loss** (`--gain` green / `--loss` red) for *signed* deltas — used on the Positions tab. Unchanged.
- **Red→yellow→green scale** for any *0–100 "higher-is-better" percentage* — via `scoreColor(pct)` in `src/scoreColor.ts` (`hsl(pct*1.2,65%,45%)`: red@0 → **yellow@50 (neutral)** → green@100). Used by the market-risk gauge and the LLM agreement metric; **use this for any future 0–100 metric.** (Backend `market_risk_score` is a 0–100 int, 50 = neutral, higher = better.)

Tokens are CSS custom properties in `src/index.css`:

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
python run_research.py --research deterministic  # or just one: deterministic | news | decision
python run_research.py --research decision --llm-runs 5   # override the ensemble size
```

**Typing:** all backend Python code is fully type-annotated (function signatures, module-level constants) and must stay that way — add type hints to any new or edited code. Dict-shaped payloads that cross module boundaries (e.g. a deterministic candidate, an LLM pick) use the `TypedDict`/`Protocol` definitions in `common/types.py` rather than bare `dict`; add new shapes there as needed. Validate with `mypy .` (run from `backend/`, inside the venv; config in `backend/mypy.ini`) — it must report no issues before committing.

`ANTHROPIC_API_KEY` is loaded from `backend/.env` (via `python-dotenv`); `.env.example` is the committed template, `.env` is gitignored — never commit the real key. `PPI_PUBLIC_API_KEY`/`PPI_PRIVATE_API_KEY` (PPI's "key pública"/"key privada") live there too, needed only when `DATA_SOURCE = "ppi"` (see the design invariants below); `scripts/check_ppi.py <TICKER>` smoke-tests the real API. `--strategy small-daily-gains` is the default. Every run writes a timestamped log (with per-approach analysis summaries) to `backend/logs/research.log`.

### Three layers: `common/` (infra) · `approaches/` (research approaches) · `strategies/` (per-strategy)

```
backend/
  common/            shared, strategy-agnostic infra: ppi_client, metrics, llm, db, log
  approaches/        the research approaches — modular siblings, run in order
    base.py          ResearchApproach interface + ordered registry
    deterministic/   (order 1) numbers-only: data → metrics → rank → store  (NO Claude)
    news/            (order 2) read today's deterministic picks → news → store  (sources.py + brief.py)
    decision/        (order 3) LLM ensemble → store each call + averaged aggregate
  strategies/
    base.py          Strategy interface + registry
    small_daily_gains/  strategy.py, config.py, research/{financial-technical,news}-approach.md
  run_research.py    CLI: --research {deterministic,news,decision,all}, --strategy, --llm-runs
  api.py             FastAPI service the frontend calls (GET /api/research|dates|research/status, POST /api/research/run — background thread). See the Frontend section for running it.
```

**Two independent axes:** *strategy* (what rules to use) and *research approach* (which stage to run). Add a strategy → a folder under `strategies/`; add an approach → a folder under `approaches/` implementing `ResearchApproach` (`name`, `order`, `run(strategy, run_dt)`) and `@register`ed. Neither touches shared code.

### The three approaches (run in order; each independently runnable, hands off via the DB)
1. **Deterministic** (`approaches/deterministic/`) — **numbers-only, no Claude, runs with no API key.** Implements the **financial-technical** methodology (`research/financial-technical-approach.md`): gathers market data, computes the three pillars (volatility=`avg_daily_range_pct`, liquidity=`avg_volume`+`spread_pct`, momentum=`momentum_today_pct`), screens (`MIN_DAILY_RANGE_PCT`) and scores 0–100 via the weights in `config.py`, stores the **top 5** picks (`FINAL_COUNT`) with a full timestamp. (Naming: the *stage* is "deterministic" — it only captures numbers; the *methodology* it implements is "financial-technical". The `.md` doc is fed to the LLM stages as context; the stage itself does not read it.)
2. **News** (`approaches/news/`) — reads **today's latest deterministic run** from the DB and researches **only those tickers** (macro/market/international always; company search skipped if there are no picks). `sources.py` prefers RSS / known URLs, falls back to a scoped Claude web-search; `brief.py` summarizes into a `NewsBrief` (macro/market/international + per-company catalyst flags). **Fetched web content is untrusted** — the summarizer never follows instructions embedded in a page. It's a **safety-veto layer**, never a re-ranker.
3. **Decision** (`approaches/decision/`) — the **final "which stocks to buy" call**, run as an **ensemble** (`--llm-runs`, default `LLM_DECISION_RUNS = 5`). Applies the catalyst veto, then makes N independent Claude calls each ranking the candidates with a short reason. **Every call is stored individually** so answers can be compared; the aggregate is a deterministic **average rank** (+ times-ranked-#1) giving an ordered recommendation and a consistency read.

### Design invariants
- **Deterministic rank; Claude judges at the decision stage; news only vetoes/warns.** The deterministic order is reproducible; the decision ensemble surfaces the LLM's judgment *and* its consistency across runs; news can exclude a catalyst stock or flag a risk-off day but never reorders.
- **Models:** news = `claude-sonnet-5`; decision = `claude-sonnet-5` (`DECISION_MODEL` in `common/llm.py`) — it's an N-call ensemble, so Sonnet by default; switch to Opus for max quality on the money decision.
- Scores are **heuristic suitability (0–100), not calibrated probabilities.** `~0.85%` round-trip cost is an estimate — re-verify against the real PPI tier.
- **Switching to the real PPI API:** set `DATA_SOURCE = "ppi"` in `strategies/small_daily_gains/config.py` (from `"mock"`) and put `PPI_PUBLIC_API_KEY`/`PPI_PRIVATE_API_KEY` in `backend/.env`. `PPI_SANDBOX` picks Sandbox vs production. `common/ppi_client.py` holds both clients — `MockPPIClient` and `PPIApiClient` (the official `ppi-client` package) — plus the `make_client()` picker; `Strategy.market_client()` is what the deterministic approach calls. Passing `run(strategy, run_dt, client=...)` explicitly still overrides everything.
- **Resetting the DB:** `backend/scripts/reset_db.sh` deletes all rows from every table (schema left intact, `VACUUM`ed after). Prompts for confirmation unless run with `-y`/`--force`.
- **DB** (`data/merval_research.db`, gitignored) stores each stage separately with a full `analysis_datetime`: `deterministic_runs`/`deterministic_picks`, `news_runs`/`news_company`, `llm_runs`/`llm_run_picks` (individual calls) + `llm_decisions`/`llm_decision_picks` (aggregate). News & decision feed from the **latest deterministic run of the current day**.

**Pre-existing trading skills** (research-only, none Merval/PPI-specific — optional future references, not used): `agiprolabs/claude-trading-skills`, `zubair-trabzada/ai-trading-claude`, `tradermonty/claude-trading-skills`, `OctagonAI/skills`. Prefer the repo's own strategy files over pulling third-party trading code (supply-chain risk; none target this market).

## Commit conventions

Use Conventional Commits for all commit messages in this repo (e.g. `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).

Keep commit messages short, concrete, and easy to understand — a single plain-language line describing what changed, no multi-paragraph bodies unless truly necessary. Do not add a Claude/AI co-author line.

## Pull requests

Ship changes as PRs, not commits straight to `main`: branch, commit, push, open a PR.

PR descriptions are for a reader who wants to know **what changed and why**, not how it was built. Say what the change does, why it was needed, and anything the reader must act on (new env vars, config to flip, follow-ups). Skip file-by-file walkthroughs, function names, and line counts — the diff already covers those. A few short sections or bullets is the right length.
