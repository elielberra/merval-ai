# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Frontend scaffolding exists (`frontend/`, React + TypeScript via Vite); no backend yet. The dashboard currently renders hardcoded dummy data — no PPI API calls are wired up (the user's PPI account isn't activated yet).

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

## Commit conventions

Use Conventional Commits for all commit messages in this repo (e.g. `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).

Keep commit messages short, concrete, and easy to understand — a single plain-language line describing what changed, no multi-paragraph bodies unless truly necessary. Do not add a Claude/AI co-author line.
