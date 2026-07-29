"""Fire N requests at the real PPI API and report status codes.

Bypasses the `ppi-client` package on purpose: it calls response.json() without
checking the status code first, so a non-200 response (empty body, HTML error
page, etc.) surfaces as a confusing JSONDecodeError instead of the real status.
This script uses `requests` directly against PPI's REST endpoints so failures
show their actual HTTP status.

Logs in once, then repeatedly calls MarketData/Current for one ticker.
Sequential by default; --mode parallel sends them concurrently.

    cd backend && source .venv/bin/activate
    python scripts/load_test_ppi.py
    python scripts/load_test_ppi.py --n 500 --mode parallel --concurrency 25
    python scripts/load_test_ppi.py --ticker YPFD --sandbox
"""

import argparse
import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from strategies.small_daily_gains import config  # noqa: E402

NUM_REQUESTS: int = 50
CONCURRENCY: int = 10
TIMEOUT_SECONDS: float = 10.0

PROD_BASE_URL = "https://clientapi.portfoliopersonal.com/api/"
SANDBOX_BASE_URL = "https://clientapisandbox.portfoliopersonal.com/api/"


class Result(NamedTuple):
    status: int | None
    error: str | None
    elapsed: float


def login(base_url: str, api_key: str, api_secret: str) -> str:
    response = requests.post(
        base_url + "1.0/Account/LoginApi",
        headers={
            "AuthorizedClient": "API_CLI_PYTHON",
            "ClientKey": "ppPYTHONSb" if base_url == SANDBOX_BASE_URL else "pp19PythonApp12",
            "ApiKey": api_key,
            "ApiSecret": api_secret,
            "Accept": "application/json",
        },
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    token: str = response.json()["accessToken"]
    return token


def send_one(url: str, token: str, sandbox: bool) -> Result:
    started = time.monotonic()
    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "AuthorizedClient": "API_CLI_PYTHON",
                "ClientKey": "ppPYTHONSb" if sandbox else "pp19PythonApp12",
            },
            timeout=TIMEOUT_SECONDS,
        )
        return Result(response.status_code, None, time.monotonic() - started)
    except Exception as exc:
        return Result(None, f"{type(exc).__name__}: {exc}", time.monotonic() - started)


def run_sequential(url: str, token: str, sandbox: bool, n: int) -> list[Result]:
    return [send_one(url, token, sandbox) for _ in range(n)]


def run_parallel(url: str, token: str, sandbox: bool, n: int, workers: int) -> list[Result]:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda _: send_one(url, token, sandbox), range(n)))


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
    parser = argparse.ArgumentParser(description="Load-test the real PPI API.")
    parser.add_argument("--n", type=int, default=NUM_REQUESTS, help="Number of requests.")
    parser.add_argument("--mode", default="sequential", choices=["sequential", "parallel"])
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY)
    parser.add_argument("--ticker", default="GGAL")
    parser.add_argument(
        "--sandbox", action="store_true", help="Use PPI's Sandbox instead of production."
    )
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    env_prefix = "PPI_SANDBOX" if args.sandbox else "PPI_PROD"
    api_key = os.getenv(f"{env_prefix}_PUBLIC_API_KEY")
    api_secret = os.getenv(f"{env_prefix}_PRIVATE_API_KEY")
    if not api_key or not api_secret:
        raise SystemExit(
            f"Missing PPI credentials: set {env_prefix}_PUBLIC_API_KEY and "
            f"{env_prefix}_PRIVATE_API_KEY in backend/.env."
        )

    base_url = SANDBOX_BASE_URL if args.sandbox else PROD_BASE_URL
    print(f"Logging in ({'sandbox' if args.sandbox else 'production'})...")
    token = login(base_url, api_key, api_secret)

    url = (
        base_url
        + f"1.0/MarketData/Current?ticker={args.ticker}"
        + f"&type={config.INSTRUMENT_TYPE}&settlement={config.SETTLEMENT}"
    )
    print(f"Sending {args.n} {args.mode} request(s) to {url}")
    if args.mode == "parallel":
        print(f"Concurrency: {args.concurrency}")

    started = time.monotonic()
    results = (
        run_sequential(url, token, args.sandbox, args.n)
        if args.mode == "sequential"
        else run_parallel(url, token, args.sandbox, args.n, args.concurrency)
    )
    report(results, time.monotonic() - started)


if __name__ == "__main__":
    main()
