"""Smoke-test the real PPI API for one ticker.

Run this the day the PPI account is activated, before flipping DATA_SOURCE to
"ppi", to confirm the responses match the shapes the deterministic stage expects:

    cd backend && source .venv/bin/activate && python scripts/check_ppi.py GGAL
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

from common.metrics import compute_metrics  # noqa: E402
from common.ppi_client import PPIApiClient  # noqa: E402
from strategies.small_daily_gains import config  # noqa: E402


def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    ticker = sys.argv[1] if len(sys.argv) > 1 else "GGAL"

    client = PPIApiClient(
        config.INSTRUMENT_TYPE, config.SETTLEMENT, not config.IS_PPI_PROD
    )
    print(f"Logged in (sandbox={not config.IS_PPI_PROD}). Querying {ticker}...\n")

    run_dt = datetime.now()
    history = client.search(
        ticker, run_dt - timedelta(days=30), run_dt, lookback_days=config.LOOKBACK_DAYS
    )
    current = client.current(ticker)
    book = client.book(ticker)

    print(f"history ({len(history)} bars), last 3:")
    for bar in history[-3:]:
        print(f"  {bar}")
    print(f"\ncurrent: {current}")
    print(f"\nbook bids[0]: {book['bids'][0] if book['bids'] else None}")
    print(f"book offers[0]: {book['offers'][0] if book['offers'] else None}")
    print(f"\nmetrics: {compute_metrics(history, current, book)}")


if __name__ == "__main__":
    main()
