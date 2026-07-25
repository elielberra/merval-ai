import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import approaches  # noqa: F401  (registers the approaches)
import strategies  # noqa: F401  (registers the strategies)
from approaches.base import get_approach, names, ordered
from common.db import init_db
from common.log import setup_logging
from strategies.base import available, get_strategy

load_dotenv(Path(__file__).resolve().parent / ".env")


def main():
    parser = argparse.ArgumentParser(description="Run Merval research approaches.")
    parser.add_argument(
        "--research", default="all", choices=["all", *names()],
        help="Which research approach to run (default: all, in order).",
    )
    parser.add_argument("--strategy", default="small-daily-gains", choices=available())
    parser.add_argument(
        "--llm-runs", type=int, default=None,
        help="Number of LLM calls in the decision ensemble (default: strategy's setting).",
    )
    args = parser.parse_args()

    log_file = setup_logging()
    init_db()
    run_dt = datetime.now()
    strategy = get_strategy(args.strategy)

    to_run = ordered() if args.research == "all" else [get_approach(args.research)]
    print(
        f"Running {[a.name for a in to_run]} for '{strategy.name}' "
        f"at {run_dt.isoformat(timespec='seconds')}\n"
    )

    for approach in to_run:
        approach.run(strategy, run_dt, llm_runs=args.llm_runs)

    print(f"\nDone. Full log (incl. analysis summaries): {log_file}")
    print("Results stored in data/merval_research.db.")


if __name__ == "__main__":
    main()
