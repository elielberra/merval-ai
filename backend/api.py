import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI

import approaches  # noqa: F401  (registers the approaches)
import strategies  # noqa: F401  (registers the strategies)
from approaches.base import ordered
from common import db
from common.log import get_logger, setup_logging
from strategies.base import get_strategy

load_dotenv(Path(__file__).resolve().parent / ".env")
setup_logging()
db.init_db()

log = get_logger("research")
log.info(
    "API started. Market data source: %s",
    get_strategy("small-daily-gains").market_source(),
)

app = FastAPI(title="merval-ai research API")

_status: dict[str, Any] = {"running": False, "error": None, "finished_at": None}
_lock = threading.Lock()


def _run_all(strategy_name: str, llm_runs: int | None) -> None:
    global _status
    try:
        db.init_db()
        strategy = get_strategy(strategy_name)
        run_dt = datetime.now()
        log.info("Research run started for strategy=%s.", strategy_name)
        for approach in ordered():
            log.info("Running %s approach...", approach.name)
            approach.run(strategy, run_dt, llm_runs=llm_runs)
        log.info("Research run complete for strategy=%s.", strategy_name)
        _status = {"running": False, "error": None, "finished_at": datetime.now().isoformat()}
    except Exception as exc:  # noqa: BLE001
        log.exception("Research run failed: %s", exc)
        _status = {"running": False, "error": str(exc), "finished_at": datetime.now().isoformat()}


@app.get("/api/dates")
def get_dates(strategy: str = "small-daily-gains") -> dict[str, list[str]]:
    return {"dates": db.list_dates(strategy)}


@app.get("/api/research")
def get_research(date: str | None = None, strategy: str = "small-daily-gains") -> dict[str, Any]:
    day = date or datetime.now().date().isoformat()
    return db.research_for_date(strategy, day)


@app.post("/api/research/run")
def run_research(strategy: str = "small-daily-gains", llm_runs: int | None = None) -> dict[str, Any]:
    global _status
    with _lock:
        if _status["running"]:
            return {"started": False, "reason": "already running"}
        _status = {"running": True, "error": None, "finished_at": None}
    threading.Thread(
        target=_run_all, args=(strategy, llm_runs), daemon=True
    ).start()
    return {"started": True}


@app.get("/api/research/status")
def research_status() -> dict[str, Any]:
    return _status
