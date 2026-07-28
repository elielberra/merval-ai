import { useCallback, useEffect, useRef, useState } from "react";

import type { Research } from "../../research/api";
import { fetchResearch, fetchStatus, triggerRun } from "../../research/api";
import { MarketRiskGauge } from "./MarketRiskGauge";
import { NewsSummary } from "./NewsSummary";
import { Spinner } from "./Spinner";
import { TopPicks } from "./TopPicks";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function missingStages(data: Research) {
  const missing: string[] = [];
  if (!data.news) missing.push("news");
  if (!data.decision) missing.push("decision");
  return missing;
}

export function ResearchTab() {
  const [date, setDate] = useState(todayISO());
  const [data, setData] = useState<Research | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  const load = useCallback(async (d: string) => {
    setLoading(true);
    try {
      setData(await fetchResearch(d));
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(date);
  }, [date, load]);

  useEffect(() => () => {
    if (pollRef.current) window.clearInterval(pollRef.current);
  }, []);

  const onRun = async () => {
    setRunning(true);
    setRunError(null);
    await triggerRun();
    pollRef.current = window.setInterval(async () => {
      const s = await fetchStatus();
      if (!s.running) {
        if (pollRef.current) window.clearInterval(pollRef.current);
        setRunning(false);
        if (s.error) {
          setRunError(s.error);
          return;
        }
        setDate(todayISO());
        await load(todayISO());
      }
    }, 3000);
  };

  const isToday = date === todayISO();
  const hasData = data?.has_data;
  const partial = hasData && !data!.is_complete;

  return (
    <div className="research">
      <div className="research-toolbar">
        <label className="date-label">
          Date
          <input
            type="date"
            value={date}
            max={todayISO()}
            onChange={(e) => setDate(e.target.value)}
          />
        </label>
      </div>

      {runError ? (
        <div className="empty-state">
          <p>Analysis failed: {runError}</p>
          <button className="btn-primary" onClick={onRun}>
            Retry analysis
          </button>
        </div>
      ) : running ? (
        <Spinner label="Running analysis… this takes ~2 minutes" />
      ) : loading ? (
        <Spinner label="Loading…" />
      ) : hasData ? (
        <>
          {partial && (
            <div className="partial-banner">
              <span>
                Incomplete analysis for {date} — the{" "}
                {missingStages(data!).join(" and ")} stage
                {missingStages(data!).length > 1 ? "s" : ""} didn't run.
              </span>
              {isToday && (
                <button className="btn-primary" onClick={onRun}>
                  Run analysis
                </button>
              )}
            </div>
          )}
          {data!.news && <MarketRiskGauge score={data!.news.market_risk_score} />}
          {data!.decision && data!.deterministic && (
            <TopPicks
              decision={data!.decision}
              deterministic={data!.deterministic.picks}
            />
          )}
          {data!.news && <NewsSummary news={data!.news} />}
        </>
      ) : (
        <div className="empty-state">
          {isToday ? (
            <>
              <p>No analysis for today yet.</p>
              <button className="btn-primary" onClick={onRun}>
                Run analysis
              </button>
            </>
          ) : (
            <p>No data for {date}.</p>
          )}
        </div>
      )}
    </div>
  );
}
