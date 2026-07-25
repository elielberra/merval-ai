#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$SCRIPT_DIR/../data/merval_research.db"

if [ ! -f "$DB_PATH" ]; then
    echo "No database found at $DB_PATH — nothing to do."
    exit 0
fi

if [[ "${1:-}" != "-y" && "${1:-}" != "--force" ]]; then
    read -r -p "This will delete ALL data in $DB_PATH. Continue? [y/N] " reply
    if [[ ! "$reply" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.executescript("""
DELETE FROM llm_decision_picks;
DELETE FROM llm_decisions;
DELETE FROM llm_run_picks;
DELETE FROM llm_runs;
DELETE FROM news_company;
DELETE FROM news_runs;
DELETE FROM deterministic_picks;
DELETE FROM deterministic_runs;
""")
conn.commit()
conn.execute("VACUUM")
conn.close()
PY

echo "Database cleared: $DB_PATH"
