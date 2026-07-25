import { useState } from "react";

import type { DecisionData, TechnicalPick } from "../../research/api";
import { scoreColor } from "../../scoreColor";
import { IndividualAnalyses } from "./IndividualAnalyses";

export function TopPicks({
  decision,
  technical,
}: {
  decision: DecisionData;
  technical: TechnicalPick[];
}) {
  const [open, setOpen] = useState(false);
  const metricsByTicker = Object.fromEntries(
    technical.map((p) => [p.ticker, p.metrics]),
  );
  const n = decision.num_runs;

  return (
    <section>
      <h2 className="section-title">
        Top picks · averaged over {n} LLM {n === 1 ? "analysis" : "analyses"}
      </h2>
      <div className="picks">
        {decision.aggregate.map((a) => {
          const m = metricsByTicker[a.ticker];
          const agreePct = n ? (a.times_first / n) * 100 : 0;
          return (
            <div className="pick-card" key={a.ticker}>
              <div className="pick-head">
                <span className="pick-rank">#{a.final_rank}</span>
                <span className="pick-ticker">{a.ticker}</span>
                <span className="pick-agree" style={{ color: scoreColor(agreePct) }}>
                  #1 in {a.times_first}/{n}
                </span>
              </div>
              {m && (
                <div className="pick-metrics">
                  <span>range {m.avg_daily_range_pct.toFixed(2)}%</span>
                  <span>vol {Math.round(m.avg_volume).toLocaleString("es-AR")}</span>
                  <span>spread {m.spread_pct.toFixed(2)}%</span>
                  <span>
                    today {m.momentum_today_pct >= 0 ? "+" : ""}
                    {m.momentum_today_pct.toFixed(2)}%
                  </span>
                </div>
              )}
              {a.why && <div className="pick-why">{a.why}</div>}
            </div>
          );
        })}
      </div>
      {decision.runs.length > 0 && (
        <button className="link-toggle" onClick={() => setOpen((o) => !o)}>
          {open
            ? "Hide individual analyses"
            : `Show the ${decision.runs.length} individual analyses`}
        </button>
      )}
      {open && <IndividualAnalyses runs={decision.runs} />}
    </section>
  );
}
