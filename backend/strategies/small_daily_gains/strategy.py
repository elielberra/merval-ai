from pathlib import Path

from strategies.base import NewsSettings, Strategy, register

from . import config

DOCS = Path(__file__).resolve().parent / "research"


def _normalize(values, invert=False):
    lo, hi = min(values), max(values)
    span = hi - lo
    out = []
    for v in values:
        n = 0.5 if span < 1e-9 else (v - lo) / span
        out.append(1 - n if invert else n)
    return out


@register
class SmallDailyGains(Strategy):
    name = "small-daily-gains"

    def watchlist(self):
        return config.WATCHLIST

    def lookback_days(self):
        return config.LOOKBACK_DAYS

    def final_count(self):
        return config.FINAL_COUNT

    def llm_decision_runs(self):
        return config.LLM_DECISION_RUNS

    def rank(self, candidates):
        screened = [
            c
            for c in candidates
            if c["metrics"]["avg_daily_range_pct"] >= config.MIN_DAILY_RANGE_PCT
        ]
        if not screened:
            return []

        range_n = _normalize([c["metrics"]["avg_daily_range_pct"] for c in screened])
        volume_n = _normalize([c["metrics"]["avg_volume"] for c in screened])
        spread_n = _normalize(
            [c["metrics"]["spread_pct"] for c in screened], invert=True
        )
        momentum_n = _normalize([c["metrics"]["momentum_today_pct"] for c in screened])

        for i, c in enumerate(screened):
            c["score"] = round(
                (
                    config.RANGE_WEIGHT * range_n[i]
                    + config.VOLUME_WEIGHT * volume_n[i]
                    + config.SPREAD_WEIGHT * spread_n[i]
                    + config.MOMENTUM_WEIGHT * momentum_n[i]
                )
                * 100,
                1,
            )

        return sorted(screened, key=lambda c: c["score"], reverse=True)

    def news_settings(self):
        return NewsSettings(
            enabled=config.NEWS_ENABLED,
            top_n=config.NEWS_TOP_N,
            macro_domains=config.NEWS_MACRO_DOMAINS,
            market_domains=config.NEWS_MARKET_DOMAINS,
            international_domains=config.NEWS_INTERNATIONAL_DOMAINS,
            company_official_domains=config.NEWS_COMPANY_OFFICIAL_DOMAINS,
            company_profiles=config.COMPANY_PROFILES,
        )

    def financial_technical_doc(self):
        return (DOCS / "financial-technical-approach.md").read_text(encoding="utf-8")

    def news_doc(self):
        return (DOCS / "news-approach.md").read_text(encoding="utf-8")
