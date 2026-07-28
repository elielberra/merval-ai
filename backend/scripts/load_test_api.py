"""Fire N requests at the research API and report status codes.

Sequential by default; --mode parallel sends them concurrently.

    cd backend && source .venv/bin/activate
    python scripts/load_test_api.py
    python scripts/load_test_api.py --n 500 --mode parallel --concurrency 25
    python scripts/load_test_api.py --path /api/research/status
"""

import argparse
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import NamedTuple

NUM_REQUESTS: int = 100
CONCURRENCY: int = 10
BASE_URL: str = "http://localhost:8000"
PATH: str = "/api/research"
TIMEOUT_SECONDS: float = 30.0


class Result(NamedTuple):
    status: int | None
    error: str | None
    elapsed: float


def send_one(url: str) -> Result:
    started = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            response.read()
            return Result(response.status, None, time.monotonic() - started)
    except urllib.error.HTTPError as exc:
        exc.read()
        return Result(exc.code, exc.reason, time.monotonic() - started)
    except Exception as exc:
        return Result(None, f"{type(exc).__name__}: {exc}", time.monotonic() - started)


def run_sequential(url: str, n: int) -> list[Result]:
    return [send_one(url) for _ in range(n)]


def run_parallel(url: str, n: int, workers: int) -> list[Result]:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda _: send_one(url), range(n)))


def is_success(result: Result) -> bool:
    return result.status is not None and 200 <= result.status < 300


def report(results: list[Result], wall_clock: float) -> None:
    successes = [r for r in results if is_success(r)]
    failures = [r for r in results if not is_success(r)]

    by_status: Counter[str] = Counter(
        str(r.status) if r.status is not None else "no response" for r in results
    )
    latencies = sorted(r.elapsed for r in results)

    print(f"\nTotal:      {len(results)}")
    print(f"Successful: {len(successes)}")
    print(f"Failed:     {len(failures)}")

    print("\nStatus codes:")
    for status, count in sorted(by_status.items()):
        print(f"  {status:>12}: {count}")

    if failures:
        errors: Counter[str] = Counter(r.error or "unknown" for r in failures)
        print("\nFailure reasons:")
        for error, count in errors.most_common():
            print(f"  {count:>4}x {error}")

    if latencies:
        print(
            f"\nLatency (s): min {latencies[0]:.3f} | "
            f"median {latencies[len(latencies) // 2]:.3f} | "
            f"max {latencies[-1]:.3f}"
        )
    print(f"Wall clock:  {wall_clock:.2f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load-test the research API.")
    parser.add_argument("--n", type=int, default=NUM_REQUESTS, help="Number of requests.")
    parser.add_argument("--mode", default="sequential", choices=["sequential", "parallel"])
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY)
    parser.add_argument("--url", default=BASE_URL)
    parser.add_argument("--path", default=PATH)
    parser.add_argument("--date", default=datetime.now().date().isoformat())
    args = parser.parse_args()

    url = f"{args.url}{args.path}"
    if args.path == PATH:
        url = f"{url}?date={args.date}"

    print(f"Sending {args.n} {args.mode} request(s) to {url}")
    if args.mode == "parallel":
        print(f"Concurrency: {args.concurrency}")

    started = time.monotonic()
    results = (
        run_sequential(url, args.n)
        if args.mode == "sequential"
        else run_parallel(url, args.n, args.concurrency)
    )
    report(results, time.monotonic() - started)


if __name__ == "__main__":
    main()
