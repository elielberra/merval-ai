import os
import random
from datetime import datetime, timedelta

from common.types import Book, BookLevel, PPIClient, PricePoint

DEFAULT_LOOKBACK_DAYS = 20


class MockPPIClient:
    def _rng(self, key: str) -> random.Random:
        return random.Random(key)

    def _base_price(self, ticker: str) -> float:
        return round(self._rng(ticker).uniform(500, 40000), 2)

    def search(
        self,
        ticker: str,
        date_from: datetime,
        date_to: datetime,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> list[PricePoint]:
        r = self._rng(ticker + "_hist")
        opening_price = self._base_price(ticker)
        typical_range = r.uniform(0.010, 0.045)
        avg_volume = r.uniform(50_000, 5_000_000)

        bars: list[PricePoint] = []
        price = opening_price
        for i in range(lookback_days):
            opening = price
            range_frac = max(0.003, r.gauss(typical_range, typical_range * 0.25))
            high = opening * (1 + range_frac / 2)
            low = opening * (1 - range_frac / 2)
            close = r.uniform(low, high)
            volume = max(1000, r.gauss(avg_volume, avg_volume * 0.3))
            bars.append(
                {
                    "date": (date_from + timedelta(days=i)).isoformat(),
                    "price": round(close, 2),
                    "volume": int(volume),
                    "openingPrice": round(opening, 2),
                    "max": round(high, 2),
                    "min": round(low, 2),
                }
            )
            price = close
        return bars

    def current(self, ticker: str) -> PricePoint:
        r = self._rng(ticker + "_current")
        opening = self._base_price(ticker)
        range_frac = r.uniform(0.005, 0.04)
        high = opening * (1 + range_frac / 2)
        low = opening * (1 - range_frac / 2)
        price = r.uniform(low, high)
        return {
            "date": datetime.now().isoformat(),
            "price": round(price, 2),
            "volume": int(r.uniform(10_000, 2_000_000)),
            "openingPrice": round(opening, 2),
            "max": round(high, 2),
            "min": round(low, 2),
        }

    def book(self, ticker: str) -> Book:
        r = self._rng(ticker + "_book")
        mid = self.current(ticker)["price"]
        spread_frac = r.uniform(0.0005, 0.006)
        best_bid = mid * (1 - spread_frac / 2)
        best_offer = mid * (1 + spread_frac / 2)
        bids: list[BookLevel] = [
            {
                "position": i + 1,
                "price": round(best_bid * (1 - 0.001 * i), 2),
                "quantity": int(r.uniform(100, 10000)),
            }
            for i in range(5)
        ]
        offers: list[BookLevel] = [
            {
                "position": i + 1,
                "price": round(best_offer * (1 + 0.001 * i), 2),
                "quantity": int(r.uniform(100, 10000)),
            }
            for i in range(5)
        ]
        return {"date": datetime.now().isoformat(), "bids": bids, "offers": offers}


class PPIApiClient:
    """The real PPI API, via the official `ppi-client` package.

    PPI's MarketData responses already have the shapes this codebase expects
    (`PricePoint`, `Book`), so they are returned as-is.
    """

    def __init__(self, instrument_type: str, settlement: str, sandbox: bool) -> None:
        from ppi_client.ppi import PPI  # the installed package, not this module

        env_prefix = "PPI_SANDBOX" if sandbox else "PPI_PROD"
        key = os.getenv(f"{env_prefix}_PUBLIC_API_KEY")
        secret = os.getenv(f"{env_prefix}_PRIVATE_API_KEY")
        if not key or not secret:
            raise RuntimeError(
                f"Missing PPI credentials: set {env_prefix}_PUBLIC_API_KEY and "
                f"{env_prefix}_PRIVATE_API_KEY in backend/.env (see .env.example), "
                "or set DATA_SOURCE = 'mock' in "
                "strategies/small_daily_gains/config.py to use mock data."
            )

        self._type = instrument_type
        self._settlement = settlement
        self._ppi = PPI(sandbox=sandbox)
        self._ppi.account.login_api(key, secret)

    def search(
        self,
        ticker: str,
        date_from: datetime,
        date_to: datetime,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> list[PricePoint]:
        bars: list[PricePoint] = self._ppi.marketdata.search(
            ticker, self._type, self._settlement, date_from, date_to
        )
        return bars[-lookback_days:]

    def current(self, ticker: str) -> PricePoint:
        point: PricePoint = self._ppi.marketdata.current(
            ticker, self._type, self._settlement
        )
        return point

    def book(self, ticker: str) -> Book:
        book: Book = self._ppi.marketdata.book(ticker, self._type, self._settlement)
        return book


def make_client(
    source: str, instrument_type: str, settlement: str, sandbox: bool
) -> PPIClient:
    if source == "ppi":
        return PPIApiClient(instrument_type, settlement, sandbox)
    return MockPPIClient()


def describe_source(source: str, sandbox: bool) -> str:
    if source == "ppi":
        return f"real PPI API ({'SANDBOX' if sandbox else 'PRODUCTION'})"
    return "MOCK data (synthetic — not real market data)"
