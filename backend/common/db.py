import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "merval_research.db"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS technical_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                analysis_datetime TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS technical_picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES technical_runs(id),
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
                technical_run_id INTEGER REFERENCES technical_runs(id),
                macro_summary TEXT,
                market_summary TEXT,
                international_summary TEXT,
                market_risk TEXT,
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
                technical_run_id INTEGER REFERENCES technical_runs(id),
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
                technical_run_id INTEGER REFERENCES technical_runs(id),
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


# --- Technical ---------------------------------------------------------------

def save_technical_run(strategy, run_dt, picks):
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO technical_runs (strategy, analysis_date, analysis_datetime,
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
                INSERT INTO technical_picks (run_id, ticker, rank, score, metrics_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, c["ticker"], c["rank"], c["score"], json.dumps(c["metrics"])),
            )
        return run_id


def latest_technical_run_today(strategy, today=None):
    """Return (run_id, picks) for the newest technical run dated today, or (None, [])."""
    today = today or date.today().isoformat()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id FROM technical_runs
            WHERE strategy = ? AND analysis_date = ?
            ORDER BY analysis_datetime DESC LIMIT 1
            """,
            (strategy, today),
        ).fetchone()
        if not row:
            return None, []
        run_id = row[0]
        picks = [
            {
                "ticker": t,
                "rank": rank,
                "score": score,
                "metrics": json.loads(metrics_json),
            }
            for t, rank, score, metrics_json in conn.execute(
                """
                SELECT ticker, rank, score, metrics_json FROM technical_picks
                WHERE run_id = ? ORDER BY rank
                """,
                (run_id,),
            )
        ]
        return run_id, picks


# --- News --------------------------------------------------------------------

def save_news_run(strategy, run_dt, technical_run_id, brief, company_rows):
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO news_runs (strategy, analysis_date, analysis_datetime,
                                   technical_run_id, macro_summary, market_summary,
                                   international_summary, market_risk, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strategy,
                run_dt.date().isoformat(),
                run_dt.isoformat(),
                technical_run_id,
                brief.macro_summary,
                brief.market_summary,
                brief.international_summary,
                brief.market_risk,
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


def latest_news_run_today(strategy, today=None):
    """Return (news_run_id, brief_fields, {ticker: {summary, has_catalyst}}) or (None, None, {})."""
    today = today or date.today().isoformat()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id, macro_summary, market_summary, international_summary, market_risk
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
            "market_risk": row[4],
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

def save_llm_run(strategy, run_dt, technical_run_id, news_run_id, run_index, model, picks):
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO llm_runs (strategy, analysis_date, analysis_datetime,
                                  technical_run_id, news_run_id, run_index, model,
                                  created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strategy,
                run_dt.date().isoformat(),
                run_dt.isoformat(),
                technical_run_id,
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
    strategy, run_dt, technical_run_id, news_run_id, num_runs, aggregate
):
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO llm_decisions (strategy, analysis_date, analysis_datetime,
                                       technical_run_id, news_run_id, num_runs,
                                       created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strategy,
                run_dt.date().isoformat(),
                run_dt.isoformat(),
                technical_run_id,
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
