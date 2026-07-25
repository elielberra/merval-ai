# Small, Consistent Daily Gains — Research Approach

This document tells the AI **what this strategy is trying to achieve** and **how to
judge which stocks are the best ones to trade today**. It is about *research and
selection only* — deciding which handful of stocks are worth trading. It says
nothing about *execution* (when exactly to buy or sell, how much to buy, when to
cut a loss). Execution is a separate concern handled elsewhere, later.

## The goal

Grow the account with **many small same-day gains** on liquid Argentine (Merval)
stocks, rather than a few big bets. Buy and sell within the same day; aim to take a
small, repeatable profit. The edge is consistency, not home runs — so the job of
this research step is to surface stocks that give the **best, cleanest chance of a
small intraday move in a predictable direction**, at low trading friction.

## What makes a stock a good candidate today

Judge each stock on three things, in this order of importance:

1. **Does it move enough to be worth trading?**
   Every buy-and-sell round trip costs roughly **0.85%** in broker commission and
   market fees. A stock that barely moves during the day can't produce a profit
   after that cost. So the stock's **typical daily price swing** (how far it
   travels between its low and high on an average day) must be comfortably larger
   than that cost. Stocks that don't clear this bar are not candidates at all —
   this is the first filter. Among the rest, a wider typical swing is better,
   because it leaves more room to capture a small gain.

2. **Is it easy to get in and out of?** (liquidity)
   Prefer stocks with **heavy trading volume** and a **tight gap between the buy
   and sell price** (the bid/ask spread). High volume means you can enter and exit
   near the quoted price without your own order pushing the price against you. A
   wide spread quietly eats into the thin profit margin and can turn a winning move
   into a losing trade, so tighter is strongly preferred.

3. **Is it already moving in a clear direction today?** (momentum)
   A stock that is already drifting **upward** from the day's opening price is a
   cleaner, lower-risk setup than one chopping sideways with no direction. Favor
   stocks whose move so far today points the right way, in line with the plain
   idea of "go with the trend, don't fight it."

## The data available to judge this

The only inputs are market data from the broker (PPI): recent daily price history,
today's live quote, and the current order book. From these, four signals are
computed for every stock, one per idea above plus the cost check:

- **`avg_daily_range_pct`** — the stock's average daily swing (how far it typically
  travels in a day), as a percentage. This drives pillar 1 (opportunity size) and
  the "worth trading" filter.
- **`avg_volume`** — average daily trading volume. Pillar 2 (liquidity).
- **`spread_pct`** — the current gap between the best buy and sell price. Pillar 2
  (lower is better).
- **`momentum_today_pct`** — how far the stock has moved from today's open. Pillar 3
  (a positive, upward move is preferred).

## How to make the call

Start by dropping any stock that doesn't move enough to beat costs. Among the
survivors, pick the ones that best combine a good-sized daily swing, strong
liquidity (high volume + tight spread), and a clear upward move today. Surface the
**top few** (currently the best 3) as the day's candidates, and for each, explain
in plain language *why* it fits this strategy — pointing to its actual numbers and
tying them back to the three pillars above. Be honest: if one of a stock's numbers
is weak (e.g. a wider spread than the others), say so rather than glossing over it.

## What this research deliberately does NOT do

- **No fundamentals or news.** The broker's market-data API only exposes price,
  volume, and the order book — so this is a purely price-and-volume ("technical")
  read. A stock that jumps on news this research can't see is a known blind spot.
- **No execution decisions.** Position size, exact entry/exit timing, stop-loss
  levels, and daily loss limits are all execution concerns, handled later — not
  here. This step only answers *which stocks*, not *how much* or *when*.
- **No promises.** This is a mechanical way to shortlist candidates, not investment
  advice and not a guarantee. Any "score" it produces is a rough suitability
  ranking, not a real probability of making money.
