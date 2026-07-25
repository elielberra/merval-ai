WATCHLIST = [
    "GGAL",
    "YPFD",
    "PAMP",
    "BMA",
    "ALUA",
    "TXAR",
    "CRES",
    "COME",
    "TGSU2",
    "SUPV",
    "BBAR",
    "CEPU",
    "TGNO4",
    "LOMA",
    "MIRG",
    "EDN",
]

INSTRUMENT_TYPE = "ACCIONES"
MARKET = "BYMA"
SETTLEMENT = "A-24HS"

LOOKBACK_DAYS = 20

# --- Selection parameters ----------------------------------------------------
# The numbers behind the research/selection step. The reasoning is documented
# in research/technical-approach.md; keep the two in sync. (Execution parameters
# — stop-loss, position size, daily loss limit — are NOT here; they belong to
# the execution layer, which is out of scope for now.)

# Estimated round-trip cost for a same-day buy+sell, as a percentage of the
# traded amount: PPI commission (~0.6% + 21% IVA, with the intraday smaller-leg
# waiver so it is effectively paid once) plus BYMA market fees (~0.05% per leg).
# Re-verify against the real PPI account tier once credentials are available.
ROUND_TRIP_COST_PCT = 0.85

# A stock is only worth trading if it typically moves enough to leave a profit
# after costs. The minimum typical daily range is set to roughly the round-trip
# cost plus a modest profit margin — stocks below this are dropped from selection.
MIN_PROFIT_MARGIN_PCT = 1.0
MIN_DAILY_RANGE_PCT = ROUND_TRIP_COST_PCT + MIN_PROFIT_MARGIN_PCT

# Scoring weights — the three pillars from research/technical-approach.md.
RANGE_WEIGHT = 0.35
VOLUME_WEIGHT = 0.25
SPREAD_WEIGHT = 0.20
MOMENTUM_WEIGHT = 0.20

FINAL_COUNT = 5

# Number of independent LLM calls the decision stage makes, then averages, to
# check answer consistency. Overridable at the CLI with --llm-runs.
LLM_DECISION_RUNS = 5

# --- News settings -----------------------------------------------------------
# Trusted sources per tier (see research/news-approach.md). Company news is
# fetched only for the top NEWS_TOP_N technical candidates.
NEWS_ENABLED = True
NEWS_TOP_N = 5

# Argentine macro + Merval-market tiers: trusted local outlets.
NEWS_MACRO_DOMAINS = ["ambito.com", "infobae.com", "indec.gob.ar", "bcra.gob.ar"]
NEWS_MARKET_DOMAINS = ["cronista.com", "ambito.com"]

# International tier: global events that tend to move the Merval (US Fed / rates,
# wars/geopolitics, global financial stress). Scoped to reputable global press.
NEWS_INTERNATIONAL_DOMAINS = [
    "reuters.com",
    "bloomberg.com",
    "ft.com",
    "wsj.com",
    "cnbc.com",
]

# Company tier: the authoritative, regulated catalyst source (kept as a scoped
# check). Broader company news is searched on the OPEN web (no domain filter),
# using each ticker's company name + US ADR (see COMPANY_PROFILES below).
NEWS_COMPANY_OFFICIAL_DOMAINS = ["byma.com.ar"]

# Ticker -> real company name + US ADR symbol (None where no major ADR). The ADR
# name/symbol gives far richer English-language earnings/M&A coverage than the
# local ticker, which is what the open-web company search keys off.
COMPANY_PROFILES = {
    "GGAL": {"name": "Grupo Financiero Galicia", "adr": "GGAL"},
    "YPFD": {"name": "YPF", "adr": "YPF"},
    "PAMP": {"name": "Pampa Energía", "adr": "PAM"},
    "BMA": {"name": "Banco Macro", "adr": "BMA"},
    "ALUA": {"name": "Aluar Aluminio Argentino", "adr": None},
    "TXAR": {"name": "Ternium Argentina", "adr": None},
    "CRES": {"name": "Cresud", "adr": "CRESY"},
    "COME": {"name": "Sociedad Comercial del Plata", "adr": None},
    "TGSU2": {"name": "Transportadora de Gas del Sur", "adr": "TGS"},
    "SUPV": {"name": "Grupo Supervielle", "adr": "SUPV"},
    "BBAR": {"name": "BBVA Argentina", "adr": "BBAR"},
    "CEPU": {"name": "Central Puerto", "adr": "CEPU"},
    "TGNO4": {"name": "Transportadora de Gas del Norte", "adr": None},
    "LOMA": {"name": "Loma Negra", "adr": "LOMA"},
    "MIRG": {"name": "Mirgor", "adr": None},
    "EDN": {"name": "Edenor", "adr": "EDN"},
}
