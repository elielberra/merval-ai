import { dummyStocks } from "../data/dummyStocks";
import { StockCard } from "./StockCard";

export function Dashboard() {
  return (
    <div className="dashboard">
      <h1 className="dashboard-title">Today's Positions</h1>
      <div className="stock-grid">
        {dummyStocks.map((stock) => (
          <StockCard key={stock.ticker} stock={stock} />
        ))}
      </div>
    </div>
  );
}
