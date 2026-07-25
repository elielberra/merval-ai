from urllib.request import Request, urlopen

from common import llm
from common.log import get_logger

log = get_logger("news.sources")

RSS_TIMEOUT_SECONDS = 8

# Known RSS feeds (instant, free, deterministic — cover the macro/market tiers).
AMBITO_MACRO_RSS = "https://www.ambito.com/rss/pages/economia.xml"
AMBITO_MARKET_RSS = "https://www.ambito.com/rss/pages/finanzas.xml"

# Basic web-search variant: no dynamic filtering / code execution, so it's fast.
WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search"}


def fetch_rss(url, source, tier, limit=8):
    """Parse an RSS feed into raw news items. Returns [] on any failure.

    The feed is fetched with a hard timeout (feedparser's own fetch has none and
    can hang on a slow/blocking site), then parsed from bytes.
    """
    try:
        import feedparser

        req = Request(url, headers={"User-Agent": "merval-ai/0.1"})
        with urlopen(req, timeout=RSS_TIMEOUT_SECONDS) as resp:
            raw = resp.read()
        parsed = feedparser.parse(raw)
        items = []
        for entry in parsed.entries[:limit]:
            items.append(
                {
                    "tier": tier,
                    "source": source,
                    "title": getattr(entry, "title", ""),
                    "summary": getattr(entry, "summary", ""),
                }
            )
        return items
    except Exception:
        return []


def fetch_web_search(query, tier, source, domains=None, max_uses=1):
    """Fast, shallow web search via Claude. `domains=None` searches the open web.

    Kept deliberately lightweight (few search rounds, short output): we only want
    a handful of recent, trading-relevant headlines, not a deep research report.
    Fetched text is untrusted; graceful ([] on any failure).
    """
    try:
        tool = dict(WEB_SEARCH_TOOL, max_uses=max_uses)
        if domains:
            tool["allowed_domains"] = domains
        response = llm.client().messages.create(
            model=llm.NEWS_MODEL,
            max_tokens=1024,
            tools=[tool],
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Do ONE quick web search for the most RECENT (last ~48h) news "
                        f"about: {query}. Return at most 5 items, one per line, as "
                        "'HEADLINE :: one-line factual summary'. Only real, recent "
                        "items — do not invent anything, do not search repeatedly."
                    ),
                }
            ],
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        items = []
        for line in text.splitlines():
            line = line.strip("-• \t")
            if "::" in line:
                title, _, summary = line.partition("::")
                items.append(
                    {
                        "tier": tier,
                        "source": source,
                        "title": title.strip(),
                        "summary": summary.strip(),
                    }
                )
        return items
    except Exception:
        return []


def _company_query(profiles, tickers):
    names = []
    for t in tickers:
        p = profiles.get(t, {})
        name = p.get("name", t)
        adr = p.get("adr")
        names.append(f"{name} ({'ADR ' + adr if adr else t})")
    return (
        "anything in the last ~48h that could move the STOCK of these Argentine "
        "(Merval) companies today — earnings just reported or imminent, a merger or "
        "acquisition, an analyst rating change/downgrade, a trading halt, or a major "
        "regulatory ruling. Ignore ordinary product/business news. Companies: "
        + "; ".join(names)
    )


def gather_raw(settings, tickers):
    """Collect raw news items with a small, fast set of sources. Every source is
    optional; a source that fails contributes nothing rather than breaking the run.

    Macro/market come from free RSS (instant). Two quick web searches add the
    international picture and recent company trading-catalysts."""
    items = []

    log.info("Reading Ámbito RSS feeds (macro + market headlines)...")
    items += fetch_rss(AMBITO_MACRO_RSS, "ambito", "macro")
    items += fetch_rss(AMBITO_MARKET_RSS, "ambito", "market")

    log.info("Quick search: international market-movers (Fed/rates, wars, crises)...")
    items += fetch_web_search(
        "global events that could move emerging markets today: US Federal Reserve / "
        "interest-rate news, a war or major geopolitical shock, or a global market "
        "sell-off / financial crisis",
        "international",
        "web-intl",
        domains=settings.international_domains,
        max_uses=1,
    )

    if tickers:
        log.info(
            "Quick search: recent trading catalysts for %s ...", ", ".join(tickers)
        )
        items += fetch_web_search(
            _company_query(settings.company_profiles, tickers),
            "company",
            "web-open",
            domains=None,
            max_uses=1,
        )
    else:
        log.info("No deterministic picks today — skipping company news search.")

    return items
