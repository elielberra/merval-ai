import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

from common.types import AggregatePick, Candidate, LLMPick, NewsBriefLike, NewsCompanyRow

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "merval_research.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS deterministic_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                analysis_datetime TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS deterministic_picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES deterministic_runs(id),
                ticker TEXT NOT NULL,
                rank INTEGER NOT NULL,
                score REAL NOT NULL,
                metrics_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS news_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                analysis_datetime TEXT NOT NULL,
                deterministic_run_id INTEGER REFERENCES deterministic_runs(id),
                macro_summary TEXT,
                market_summary TEXT,
                international_summary TEXT,
                market_risk_score INTEGER,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS news_company (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_run_id INTEGER NOT NULL REFERENCES news_runs(id),
                ticker TEXT NOT NULL,
                summary TEXT,
                has_catalyst INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS llm_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                analysis_datetime TEXT NOT NULL,
                deterministic_run_id INTEGER REFERENCES deterministic_runs(id),
                news_run_id INTEGER REFERENCES news_runs(id),
                run_index INTEGER NOT NULL,
                model TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS llm_run_picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                llm_run_id INTEGER NOT NULL REFERENCES llm_runs(id),
                ticker TEXT NOT NULL,
                rank INTEGER NOT NULL,
                reason TEXT
            );

            CREATE TABLE IF NOT EXISTS llm_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                analysis_datetime TEXT NOT NULL,
                deterministic_run_id INTEGER REFERENCES deterministic_runs(id),
                news_run_id INTEGER REFERENCES news_runs(id),
                num_runs INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS llm_decision_picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                llm_decision_id INTEGER NOT NULL REFERENCES llm_decisions(id),
                ticker TEXT NOT NULL,
                final_rank INTEGER NOT NULL,
                avg_rank REAL NOT NULL,
                times_first INTEGER NOT NULL,
                why TEXT
            );
            """
        )


# --- Deterministic -----------------------------------------------------------

def save_deterministic_run(strategy: str, run_dt: datetime, picks: list[Candidate]) -> int | None:
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO deterministic_runs (strategy, analysis_date, analysis_datetime,
                                        created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                strategy,
                run_dt.date().isoformat(),
                run_dt.isoformat(),
                datetime.now().isoformat(),
            ),
        )
        run_id = cur.lastrowid
        for c in picks:
            conn.execute(
                """
                INSERT INTO deterministic_picks (run_id, ticker, rank, score, metrics_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, c["ticker"], c["rank"], c["score"], json.dumps(c["metrics"])),
            )
        return run_id


def latest_deterministic_run_today(
    strategy: str, today: str | None = None
) -> tuple[int | None, list[Candidate]]:
    """Return (run_id, picks) for the newest deterministic run dated today, or (None, [])."""
    today = today or date.today().isoformat()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id FROM deterministic_runs
            WHERE strategy = ? AND analysis_date = ?
            ORDER BY analysis_datetime DESC LIMIT 1
            """,
            (strategy, today),
        ).fetchone()
        if not row:
            return None, []
        run_id = row[0]
        picks: list[Candidate] = [
            {
                "ticker": t,
                "rank": rank,
                "score": score,
                "metrics": json.loads(metrics_json),
            }
            for t, rank, score, metrics_json in conn.execute(
                """
                SELECT ticker, rank, score, metrics_json FROM deterministic_picks
                WHERE run_id = ? ORDER BY rank
                """,
                (run_id,),
            )
        ]
        return run_id, picks


# --- News --------------------------------------------------------------------

def save_news_run(
    strategy: str,
    run_dt: datetime,
    deterministic_run_id: int | None,
    brief: NewsBriefLike,
    company_rows: list[NewsCompanyRow],
) -> int | None:
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO news_runs (strategy, analysis_date, analysis_datetime,
                                   deterministic_run_id, macro_summary, market_summary,
                                   international_summary, market_risk_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strategy,
                run_dt.date().isoformat(),
                run_dt.isoformat(),
                deterministic_run_id,
                brief.macro_summary,
                brief.market_summary,
                brief.international_summary,
                brief.market_risk_score,
                datetime.now().isoformat(),
            ),
        )
        news_run_id = cur.lastrowid
        for r in company_rows:
            conn.execute(
                """
                INSERT INTO news_company (news_run_id, ticker, summary, has_catalyst)
                VALUES (?, ?, ?, ?)
                """,
                (news_run_id, r["ticker"], r.get("summary"), 1 if r.get("has_catalyst") else 0),
            )
        return news_run_id


def latest_news_run_today(
    strategy: str, today: str | None = None
) -> tuple[int | None, dict[str, Any] | None, dict[str, dict[str, Any]]]:
    """Return (news_run_id, brief_fields, {ticker: {summary, has_catalyst}}) or (None, None, {})."""
    today = today or date.today().isoformat()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id, macro_summary, market_summary, international_summary,
                   market_risk_score
            FROM news_runs
            WHERE strategy = ? AND analysis_date = ?
            ORDER BY analysis_datetime DESC LIMIT 1
            """,
            (strategy, today),
        ).fetchone()
        if not row:
            return None, None, {}
        news_run_id = row[0]
        fields = {
            "macro_summary": row[1],
            "market_summary": row[2],
            "international_summary": row[3],
            "market_risk_score": row[4],
        }
        companies = {
            t: {"summary": summary, "has_catalyst": bool(has_catalyst)}
            for t, summary, has_catalyst in conn.execute(
                "SELECT ticker, summary, has_catalyst FROM news_company WHERE news_run_id = ?",
                (news_run_id,),
            )
        }
        return news_run_id, fields, companies


# --- LLM decision ------------------------------------------------------------

def save_llm_run(
    strategy: str,
    run_dt: datetime,
    deterministic_run_id: int | None,
    news_run_id: int | None,
    run_index: int,
    model: str,
    picks: list[LLMPick],
) -> int | None:
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO llm_runs (strategy, analysis_date, analysis_datetime,
                                  deterministic_run_id, news_run_id, run_index, model,
                                  created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strategy,
                run_dt.date().isoformat(),
                run_dt.isoformat(),
                deterministic_run_id,
                news_run_id,
                run_index,
                model,
                datetime.now().isoformat(),
            ),
        )
        llm_run_id = cur.lastrowid
        for p in picks:
            conn.execute(
                """
                INSERT INTO llm_run_picks (llm_run_id, ticker, rank, reason)
                VALUES (?, ?, ?, ?)
                """,
                (llm_run_id, p["ticker"], p["rank"], p.get("reason")),
            )
        return llm_run_id


def save_llm_decision(
    strategy: str,
    run_dt: datetime,
    deterministic_run_id: int | None,
    news_run_id: int | None,
    num_runs: int,
    aggregate: list[AggregatePick],
) -> int | None:
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO llm_decisions (strategy, analysis_date, analysis_datetime,
                                       deterministic_run_id, news_run_id, num_runs,
                                       created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strategy,
                run_dt.date().isoformat(),
                run_dt.isoformat(),
                deterministic_run_id,
                news_run_id,
                num_runs,
                datetime.now().isoformat(),
            ),
        )
        decision_id = cur.lastrowid
        for a in aggregate:
            conn.execute(
                """
                INSERT INTO llm_decision_picks (llm_decision_id, ticker, final_rank,
                                                avg_rank, times_first, why)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    a["ticker"],
                    a["final_rank"],
                    a["avg_rank"],
                    a["times_first"],
                    a.get("why"),
                ),
            )
        return decision_id


# --- Read helpers for the API ------------------------------------------------

def list_dates(strategy: str) -> list[str]:
    """Dates (newest first) that have at least one deterministic run."""
    with _connect() as conn:
        return [
            r[0]
            for r in conn.execute(
                """
                SELECT DISTINCT analysis_date FROM deterministic_runs
                WHERE strategy = ? ORDER BY analysis_date DESC
                """,
                (strategy,),
            )
        ]


def research_for_date(strategy: str, day: str) -> dict[str, Any]:
    """Assemble the latest deterministic/news/decision runs for a given date into
    a single dict for the frontend. `has_data` is False when there's no run;
    `is_complete` is False when only some of the three stages ran that day."""
    det_run_id, picks = latest_deterministic_run_today(strategy, day)
    if det_run_id is None:
        return {"date": day, "has_data": False, "is_complete": False}

    with _connect() as conn:
        det_dt = conn.execute(
            "SELECT analysis_datetime FROM deterministic_runs WHERE id = ?", (det_run_id,)
        ).fetchone()[0]

        result: dict[str, Any] = {
            "date": day,
            "has_data": True,
            "deterministic": {"run_datetime": det_dt, "picks": picks},
            "news": None,
            "decision": None,
        }

        _news_run_id, fields, companies = latest_news_run_today(strategy, day)
        if fields is not None:
            result["news"] = {
                **fields,
                "companies": [
                    {"ticker": t, **v} for t, v in companies.items()
                ],
            }

        drow = conn.execute(
            """
            SELECT id, analysis_datetime, num_runs FROM llm_decisions
            WHERE strategy = ? AND analysis_date = ?
            ORDER BY analysis_datetime DESC LIMIT 1
            """,
            (strategy, day),
        ).fetchone()
        if drow:
            decision_id, decision_dt, num_runs = drow
            aggregate = [
                {
                    "ticker": t,
                    "final_rank": fr,
                    "avg_rank": ar,
                    "times_first": tf,
                    "why": why,
                }
                for t, fr, ar, tf, why in conn.execute(
                    """
                    SELECT ticker, final_rank, avg_rank, times_first, why
                    FROM llm_decision_picks WHERE llm_decision_id = ?
                    ORDER BY final_rank
                    """,
                    (decision_id,),
                )
            ]
            runs = []
            for run_id, run_index, model in conn.execute(
                """
                SELECT id, run_index, model FROM llm_runs
                WHERE strategy = ? AND analysis_datetime = ?
                ORDER BY run_index
                """,
                (strategy, decision_dt),
            ):
                run_picks = [
                    {"ticker": t, "rank": rk, "reason": rs}
                    for t, rk, rs in conn.execute(
                        """
                        SELECT ticker, rank, reason FROM llm_run_picks
                        WHERE llm_run_id = ? ORDER BY rank
                        """,
                        (run_id,),
                    )
                ]
                runs.append({"run_index": run_index, "model": model, "picks": run_picks})
            result["decision"] = {
                "num_runs": num_runs,
                "aggregate": aggregate,
                "runs": runs,
            }

        result["is_complete"] = result["news"] is not None and result["decision"] is not None
        return result


# --- Deletion ------------------------------------------------------------

_DATE_RANGE_DELETIONS: list[tuple[str, str]] = [
    (
        "llm_decision_picks",
        "DELETE FROM llm_decision_picks WHERE llm_decision_id IN "
        "(SELECT id FROM llm_decisions WHERE analysis_date BETWEEN ? AND ?)",
    ),
    (
        "llm_run_picks",
        "DELETE FROM llm_run_picks WHERE llm_run_id IN "
        "(SELECT id FROM llm_runs WHERE analysis_date BETWEEN ? AND ?)",
    ),
    ("llm_decisions", "DELETE FROM llm_decisions WHERE analysis_date BETWEEN ? AND ?"),
    ("llm_runs", "DELETE FROM llm_runs WHERE analysis_date BETWEEN ? AND ?"),
    (
        "news_company",
        "DELETE FROM news_company WHERE news_run_id IN "
        "(SELECT id FROM news_runs WHERE analysis_date BETWEEN ? AND ?)",
    ),
    ("news_runs", "DELETE FROM news_runs WHERE analysis_date BETWEEN ? AND ?"),
    (
        "deterministic_picks",
        "DELETE FROM deterministic_picks WHERE run_id IN "
        "(SELECT id FROM deterministic_runs WHERE analysis_date BETWEEN ? AND ?)",
    ),
    ("deterministic_runs", "DELETE FROM deterministic_runs WHERE analysis_date BETWEEN ? AND ?"),
]

_ALL_TABLES_DELETE_ORDER: list[str] = [table for table, _ in _DATE_RANGE_DELETIONS]


def delete_date_range(start_date: str, end_date: str) -> dict[str, int]:
    """Delete all research data with analysis_date in [start_date, end_date]
    (inclusive, both "YYYY-MM-DD"). Returns rows deleted per table."""
    with _connect() as conn:
        return {
            table: conn.execute(sql, (start_date, end_date)).rowcount
            for table, sql in _DATE_RANGE_DELETIONS
        }


def purge_all() -> dict[str, int]:
    """Delete every row from every research table and reclaim disk space.
    Returns rows deleted per table."""
    with _connect() as conn:
        counts = {
            table: conn.execute(f"DELETE FROM {table}").rowcount
            for table in _ALL_TABLES_DELETE_ORDER
        }
    with _connect() as conn:
        conn.execute("VACUUM")
    return counts
