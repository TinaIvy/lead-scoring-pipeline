"""Run the whole pipeline once: read, score, build conversions, upload, log.

Safety features, because this kind of job changes what an ad account spends:

- Dry run by default. Nothing is uploaded unless `live=True`.
- A kill switch. Set the environment variable PIPELINE_ENABLED=0 and the run
  stops before doing anything.
- A run log. Every run, including skipped and failed ones, adds one line to a
  JSON Lines file, so you can see later what happened.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from .conversions import DEFAULT_MIN_SCORE, build_conversions
from .loader import load_leads
from .uploader import RateLimitError, upload_with_retry


def _append_log(log_path, run):
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(run) + "\n")


def run_pipeline(
    leads_path,
    client,
    log_path,
    *,
    live=False,
    min_score=DEFAULT_MIN_SCORE,
    output_path=None,
    env=None,
    sleep=time.sleep,
    now=None,
):
    """Run the pipeline once and return a summary dictionary of what happened.

    `env`, `sleep` and `now` can be replaced in tests, so tests can set the kill
    switch, skip waiting and use a fixed clock.
    """
    env = os.environ if env is None else env
    now = now or (lambda: datetime.now(timezone.utc))

    run = {
        "timestamp": now().isoformat(),
        "mode": "live" if live else "dry_run",
        "min_score": min_score,
    }

    if env.get("PIPELINE_ENABLED", "1") == "0":
        run["status"] = "disabled"
        _append_log(log_path, run)
        return run

    try:
        leads = load_leads(leads_path)
        batch = build_conversions(leads, min_score)
        run.update(
            leads_read=len(leads),
            conversions_ready=len(batch.conversions),
            skipped=batch.skipped,
        )
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(json.dumps(batch.conversions, indent=2), encoding="utf-8")

        if not live:
            run["status"] = "dry_run"
        elif not batch.conversions:
            run.update(status="nothing_to_upload", uploaded=0)
        else:
            run["uploaded"] = upload_with_retry(client, batch.conversions, sleep=sleep)
            run["status"] = "uploaded"
    except RateLimitError as error:
        run.update(status="failed", error=f"gave up after repeated rate limits: {error}")
    except (OSError, ValueError) as error:
        run.update(status="failed", error=str(error))

    _append_log(log_path, run)
    return run
