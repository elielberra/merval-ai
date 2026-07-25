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

export function ResearchTab() {
  const [date, setDate] = useState(todayISO());
  const [data, setData] = useState<Research | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
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
    await triggerRun();
    pollRef.current = window.setInterval(async () => {
      const s = await fetchStatus();
      if (!s.running) {
        if (pollRef.current) window.clearInterval(pollRef.current);
        setRunning(false);
        setDate(todayISO());
        await load(todayISO());
      }
    }, 3000);
  };

  const isToday = date === todayISO();
  const hasData = data?.has_data;

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

      {running ? (
        <Spinner label="Running analysis… this takes ~2 minutes" />
      ) : loading ? (
        <Spinner label="Loading…" />
      ) : hasData ? (
        <>
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
