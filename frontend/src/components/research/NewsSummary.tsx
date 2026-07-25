import type { NewsData } from "../../research/api";

export function NewsSummary({ news }: { news: NewsData }) {
  return (
    <section>
      <h2 className="section-title">News summary</h2>
      <div className="news-card">
        <div className="news-block">
          <span className="news-label">Macro</span>
          <p>{news.macro_summary || "—"}</p>
        </div>
        <div className="news-block">
          <span className="news-label">Market</span>
          <p>{news.market_summary || "—"}</p>
        </div>
        <div className="news-block">
          <span className="news-label">International</span>
          <p>{news.international_summary || "—"}</p>
        </div>
        {news.companies.length > 0 && (
          <div className="news-block">
            <span className="news-label">Companies</span>
            <ul className="news-companies">
              {news.companies.map((c) => (
                <li key={c.ticker}>
                  <strong>{c.ticker}</strong>
                  {c.has_catalyst && <span className="catalyst-tag">catalyst</span>} —{" "}
                  {c.summary || "no news"}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
