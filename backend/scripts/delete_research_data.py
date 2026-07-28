"""Delete research data for a single date or a date range.

Dates are in ISO format: YYYY-MM-DD (e.g. 2026-07-20).

    cd backend && source .venv/bin/activate
    python scripts/delete_research_data.py --date 2026-07-20
    python scripts/delete_research_data.py --start 2026-07-01 --end 2026-07-15
    python scripts/delete_research_data.py --date 2026-07-20 -y
    python scripts/delete_research_data.py --today
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.db import delete_date_range  # noqa: E402


def _parse_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date {value!r}, expected YYYY-MM-DD")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--date", type=_parse_date, help="single date to delete, format YYYY-MM-DD")
    parser.add_argument(
        "--start", type=_parse_date, help="start of range, inclusive, format YYYY-MM-DD"
    )
    parser.add_argument(
        "--end", type=_parse_date, help="end of range, inclusive, format YYYY-MM-DD"
    )
    parser.add_argument("--today", action="store_true", help="delete today's research data")
    parser.add_argument("-y", "--force", action="store_true", help="skip confirmation prompt")
    args = parser.parse_args()

    modes_given = sum(bool(x) for x in (args.date, args.today, args.start or args.end))
    if modes_given > 1:
        parser.error("use only one of --date, --today, or --start/--end")
    if bool(args.start) != bool(args.end):
        parser.error("--start and --end must be given together")
    if modes_given == 0:
        parser.error("must pass --date, --today, or --start/--end")
    if args.start and args.end and args.start > args.end:
        parser.error("--start must not be after --end")
    if args.today:
        args.date = date.today().isoformat()
    return args


def main() -> None:
    args = parse_args()
    start_date: str = args.date or args.start
    end_date: str = args.date or args.end
    label = start_date if start_date == end_date else f"{start_date} to {end_date}"

    if not args.force:
        reply = input(f"This will delete all research data for {label}. Continue? [y/N] ")
        if reply.strip().lower() != "y":
            print("Aborted.")
            return

    counts = delete_date_range(start_date, end_date)
    total = sum(counts.values())
    if total == 0:
        print(f"No data found for {label}.")
        return

    for table, n in counts.items():
        if n:
            print(f"  {table}: {n}")
    print(f"Deleted {total} rows for {label}.")


if __name__ == "__main__":
    main()
