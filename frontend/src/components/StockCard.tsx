import type { Stock } from "../types";

function getBand(absPercent: number): "subtle" | "moderate" | "strong" {
  if (absPercent < 1) return "subtle";
  if (absPercent < 3) return "moderate";
  return "strong";
}

export function StockCard({ stock }: { stock: Stock }) {
  const diffPercent =
    ((stock.currentPrice - stock.boughtPrice) / stock.boughtPrice) * 100;
  const isGain = diffPercent >= 0;
  const band = getBand(Math.abs(diffPercent));
  const badgeClass = `diff-badge ${isGain ? "gain" : "loss"} ${band}`;
  const sign = isGain ? "+" : "−";

  return (
    <div className="stock-card">
      <div className="stock-header">
        <span className="stock-ticker">{stock.ticker}</span>
        <span className="stock-description">{stock.description}</span>
      </div>

      <div className="stock-prices">
        <div className="price-block">
          <span className="price-label">Bought</span>
          <span className="price-value">
            {stock.boughtPrice.toLocaleString("es-AR", {
              minimumFractionDigits: 2,
            })}
          </span>
        </div>
        <div className="price-block">
          <span className="price-label">Current</span>
          <span className="price-value">
            {stock.currentPrice.toLocaleString("es-AR", {
              minimumFractionDigits: 2,
            })}
          </span>
        </div>
        <div className="price-block">
          <span className="price-label">Change</span>
          <span className={badgeClass}>
            {sign}
            {Math.abs(diffPercent).toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="stock-actions">
        <button className="btn-outline">Sell Now</button>
        <button className="btn-outline">Create Sell Order</button>
      </div>
    </div>
  );
}
