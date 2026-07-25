def compute_metrics(history, current, book):
    ranges = []
    volumes = []
    for bar in history:
        opening = bar["openingPrice"]
        if opening > 0:
            ranges.append((bar["max"] - bar["min"]) / opening * 100)
        volumes.append(bar["volume"])

    avg_daily_range_pct = sum(ranges) / len(ranges) if ranges else 0.0
    avg_volume = sum(volumes) / len(volumes) if volumes else 0.0

    best_bid = book["bids"][0]["price"] if book["bids"] else 0.0
    best_offer = book["offers"][0]["price"] if book["offers"] else 0.0
    mid = (best_bid + best_offer) / 2 if best_bid and best_offer else 0.0
    spread_pct = (best_offer - best_bid) / mid * 100 if mid > 0 else 0.0

    opening = current["openingPrice"]
    momentum_today_pct = (
        (current["price"] - opening) / opening * 100 if opening > 0 else 0.0
    )

    return {
        "avg_daily_range_pct": round(avg_daily_range_pct, 4),
        "avg_volume": round(avg_volume, 2),
        "spread_pct": round(spread_pct, 4),
        "momentum_today_pct": round(momentum_today_pct, 4),
    }
