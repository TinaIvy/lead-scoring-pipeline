"""Command line entry point:  python -m lead_pipeline"""

import argparse

from .conversions import DEFAULT_MIN_SCORE
from .pipeline import run_pipeline
from .uploader import FakeAdsClient


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score leads and prepare ad conversions.")
    parser.add_argument("--leads", default="data/leads.csv", help="CSV file of leads")
    parser.add_argument("--log", default="logs/run_log.jsonl", help="where to append the run log")
    parser.add_argument("--output", default=None, help="also write the conversions to this JSON file")
    parser.add_argument("--min-score", type=int, default=DEFAULT_MIN_SCORE)
    parser.add_argument(
        "--live",
        action="store_true",
        help="upload to the (simulated) ad platform instead of doing a dry run",
    )
    parser.add_argument(
        "--simulate-rate-limits",
        type=int,
        default=0,
        metavar="N",
        help="make the first N uploads fail, to show the retry logic (needs --live)",
    )
    args = parser.parse_args(argv)

    client = FakeAdsClient(fail_first_calls=args.simulate_rate_limits)
    run = run_pipeline(
        args.leads,
        client,
        args.log,
        live=args.live,
        min_score=args.min_score,
        output_path=args.output,
    )

    print(f"Status: {run['status']} ({run['mode']})")
    if "leads_read" in run:
        print(f"Leads read: {run['leads_read']}")
        print(f"Conversions ready: {run['conversions_ready']}")
        print(f"Skipped: {run['skipped']}")
    if "uploaded" in run:
        print(f"Uploaded: {run['uploaded']}  (simulated, no real ad platform was contacted)")
    if "error" in run:
        print(f"Error: {run['error']}")
    print(f"Run logged to {args.log}")
    return 1 if run["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
