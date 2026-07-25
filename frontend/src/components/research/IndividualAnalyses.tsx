import type { LlmRun } from "../../research/api";

export function IndividualAnalyses({ runs }: { runs: LlmRun[] }) {
  return (
    <div className="analyses">
      {runs.map((run) => (
        <div className="analysis-card" key={run.run_index}>
          <div className="analysis-head">
            Analysis #{run.run_index}{" "}
            <span className="analysis-model">({run.model})</span>
          </div>
          <ol className="analysis-list">
            {[...run.picks]
              .sort((a, b) => a.rank - b.rank)
              .map((p) => (
                <li key={p.ticker}>
                  <strong>{p.ticker}</strong>
                  {p.reason ? ` — ${p.reason}` : ""}
                </li>
              ))}
          </ol>
        </div>
      ))}
    </div>
  );
}
