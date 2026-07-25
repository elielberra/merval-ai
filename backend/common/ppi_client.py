import random
from datetime import datetime, timedelta

DEFAULT_LOOKBACK_DAYS = 20


class MockPPIClient:
    def _rng(self, key):
        return random.Random(key)

    def _base_price(self, ticker):
        return round(self._rng(ticker).uniform(500, 40000), 2)

    def search(self, ticker, date_from, date_to, lookback_days=DEFAULT_LOOKBACK_DAYS):
        r = self._rng(ticker + "_hist")
        opening_price = self._base_price(ticker)
        typical_range = r.uniform(0.010, 0.045)
        avg_volume = r.uniform(50_000, 5_000_000)

        bars = []
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

    def current(self, ticker):
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

    def book(self, ticker):
        r = self._rng(ticker + "_book")
        mid = self.current(ticker)["price"]
        spread_frac = r.uniform(0.0005, 0.006)
        best_bid = mid * (1 - spread_frac / 2)
        best_offer = mid * (1 + spread_frac / 2)
        bids = [
            {
                "position": i + 1,
                "price": round(best_bid * (1 - 0.001 * i), 2),
                "quantity": int(r.uniform(100, 10000)),
            }
            for i in range(5)
        ]
        offers = [
            {
                "position": i + 1,
                "price": round(best_offer * (1 + 0.001 * i), 2),
                "quantity": int(r.uniform(100, 10000)),
            }
            for i in range(5)
        ]
        return {"date": datetime.now().isoformat(), "bids": bids, "offers": offers}
