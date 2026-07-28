"""Delete ALL research data from the database (every date, every strategy).

    cd backend && source .venv/bin/activate
    python scripts/purge_db.py
    python scripts/purge_db.py -y
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.db import DB_PATH, purge_all  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-y", "--force", action="store_true", help="skip confirmation prompt")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"No database found at {DB_PATH} — nothing to do.")
        return

    if not args.force:
        reply = input(f"This will delete ALL data in {DB_PATH}. Continue? [y/N] ")
        if reply.strip().lower() != "y":
            print("Aborted.")
            return

    counts = purge_all()
    total = sum(counts.values())
    print(f"Database purged: {total} rows deleted from {DB_PATH}")


if __name__ == "__main__":
    main()
