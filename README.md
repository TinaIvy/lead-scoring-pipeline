# Lead Scoring Pipeline

![Tests](https://github.com/TinaIvy/lead-scoring-pipeline/actions/workflows/tests.yml/badge.svg)

A small Python project that scores leads on how far they actually progressed, then prepares the good ones as **offline conversions** to send back to an ad platform.

The idea: an ad platform optimises for whatever it is told counts as a "conversion". If every form fill counts equally, it learns to find people who fill in forms. If conversions reflect lead *quality* (a long call, a booked appointment, a kept appointment, a payment), it learns to find people like your best customers.

Everything here uses made-up data. The upload is **simulated**: no real ad platform is contacted, and there are no keys or credentials anywhere in the project.

## What it does

1. **Reads** a CSV of leads and rejects bad data with the line number, instead of scoring it anyway.
2. **Scores** each lead from 0 to 100:

   | Signal | Points |
   | --- | --- |
   | Call length: 30 s / 2 min / 5 min or more | 10 / 20 / 30 |
   | Appointment booked | 25 |
   | Appointment attended | 25 |
   | Payment: any / $500 or more | 10 / 20 |

3. **Builds conversions** for leads that came from an ad click (they have a click id), score at least 40, and are not a repeat of a better lead from the same click.
4. **Uploads** them to a simulated ad platform, retrying with growing waits when it answers "slow down".
5. **Logs** every run, successful or not, as one line of JSON.

## Safety features

This kind of job changes what an ad account spends, so it is built to fail safely:

- **Dry run by default.** Nothing is uploaded unless you pass `--live`.
- **Kill switch.** Set `PIPELINE_ENABLED=0` and a run stops before doing anything. The stop is logged.
- **Retries with backoff.** Rate limit errors are retried after 1, 2, then 4 seconds. Other errors are not retried, because repeating a real bug does not fix it.
- **Failures are logged, not hidden.** A bad data file or a platform that stays unavailable ends in a `failed` log entry and a non-zero exit code.
- **Strict input checks.** An appointment cannot be attended without being booked, amounts cannot be negative, a lead id cannot appear twice.

## Example run

Dry run on the 83 made-up leads:

```
$ python -m lead_pipeline
Status: dry_run (dry_run)
Leads read: 83
Conversions ready: 32
Skipped: {'no_gclid': 30, 'below_min_score': 18, 'duplicate_gclid': 3}
Run logged to logs/run_log.jsonl
```

Live run, with the first two uploads made to fail so the retry logic is visible:

```
$ python -m lead_pipeline --live --simulate-rate-limits 2
Status: uploaded (live)
Leads read: 83
Conversions ready: 32
Skipped: {'no_gclid': 30, 'below_min_score': 18, 'duplicate_gclid': 3}
Uploaded: 32  (simulated, no real ad platform was contacted)
Run logged to logs/run_log.jsonl
```

One conversion record:

```json
{
  "gclid": "FAKE-GCLID-0052",
  "conversion_action": "lead_quality_high",
  "conversion_date_time": "2026-03-01 12:00:00+00:00",
  "conversion_value": 90.0,
  "currency_code": "USD"
}
```

## Run it

You need Python 3.10 or newer.

```bash
git clone https://github.com/TinaIvy/lead-scoring-pipeline.git
cd lead-scoring-pipeline

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest                                          # run the tests
python -m lead_pipeline                         # dry run
python -m lead_pipeline --output output/conversions.json   # also save the conversions
python -m lead_pipeline --live                  # simulated upload
PIPELINE_ENABLED=0 python -m lead_pipeline      # try the kill switch
```

To make a fresh set of made-up leads: `python scripts/generate_fake_leads.py`. The random seed is fixed, so it produces the same file every time.

## Project layout

```
data/leads.csv                  83 made-up leads
scripts/generate_fake_leads.py  Creates the made-up data
src/lead_pipeline/
    models.py                   The Lead type
    loader.py                   Reads and validates the CSV
    scoring.py                  Score and tier rules
    conversions.py              Chooses leads to report, de-duplicates, builds records
    uploader.py                 Simulated platform and the retry logic
    pipeline.py                 Runs everything once: kill switch, dry run, log
    __main__.py                 Command line
tests/                          Automated tests (pytest)
```

## Design choices

- **The score is a handful of visible rules**, not a model. Each rule can be explained to a non-technical colleague and changed in one line. A trained model would need far more data than a demo has.
- **Waiting and the clock can be replaced.** The pipeline takes `sleep`, `now` and the environment as inputs, so the tests run instantly and can set the kill switch without touching the real environment.
- **The ad platform is a swappable object.** `FakeAdsClient` has one method, `upload_conversions`. A real client with the same method would slot in without changing the pipeline.
- **A click is reported once.** When two leads come from the same click, the higher-scoring one wins.

## Limitations

- The upload is simulated. A real version needs the platform's API, authentication, and its exact conversion format and time zone rules.
- The scoring weights are illustrative, not tuned on outcomes. A real version would check which signals actually predict revenue.
- Conversions are uploaded in one batch. Real platforms limit batch sizes.
- Conversion times use a fixed noon UTC because the sample data has dates only.

## Next steps

- Compare the scored tiers with actual revenue and adjust the weights.
- Split uploads into batches and report which records the platform rejected.
- Add a scheduled run and an alert when a run fails.

## License

MIT
