import { scoreColor } from "../../scoreColor";

function band(score: number): string {
  if (score >= 66) return "Good day to trade";
  if (score >= 34) return "Neutral conditions";
  return "Poor day to trade";
}

export function MarketRiskGauge({ score }: { score: number }) {
  const color = scoreColor(score);
  return (
    <section className="gauge-card">
      <div className="gauge-title">Trading conditions today</div>
      <div className="gauge-row">
        <div className="gauge-number" style={{ color }}>
          {score}
          <span className="gauge-max">/100</span>
        </div>
        <div className="gauge-meter">
          <div className="gauge-fill" style={{ width: `${score}%`, background: color }} />
          <div className="gauge-mid" title="50 = neutral" />
        </div>
      </div>
      <div className="gauge-caption" style={{ color }}>
        {band(score)} <span className="gauge-note">(50 = neutral)</span>
      </div>
    </section>
  );
}
