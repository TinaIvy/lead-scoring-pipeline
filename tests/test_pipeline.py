import json
from datetime import datetime, timezone

from helpers import make_row, write_csv

from lead_pipeline.pipeline import run_pipeline
from lead_pipeline.uploader import FakeAdsClient

FIXED_TIME = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)


def fixed_clock():
    return FIXED_TIME


def sample_leads_file(tmp_path):
    """Four leads: two reportable, one too weak, one without a click id."""
    rows = [
        make_row(
            lead_id="L1",
            gclid="G1",
            call_seconds="300",
            appointment_booked="1",
            appointment_attended="1",
            payment_amount="600",
        ),  # 100 points
        make_row(lead_id="L2", gclid="G2", call_seconds="130", appointment_booked="1"),  # 45
        make_row(lead_id="L3", gclid="G3", call_seconds="10"),  # 0
        make_row(lead_id="L4", gclid="", call_seconds="300", appointment_booked="1"),  # no click
    ]
    return write_csv(tmp_path / "leads.csv", rows)


def run(tmp_path, client=None, **options):
    client = client or FakeAdsClient()
    options.setdefault("env", {})
    options.setdefault("sleep", lambda seconds: None)
    options.setdefault("now", fixed_clock)
    log_path = tmp_path / "logs" / "run_log.jsonl"
    result = run_pipeline(sample_leads_file(tmp_path), client, log_path, **options)
    return result, client, log_path


def read_log(log_path):
    return [json.loads(line) for line in log_path.read_text().splitlines()]


def test_dry_run_is_the_default_and_uploads_nothing(tmp_path):
    result, client, _ = run(tmp_path)
    assert result["status"] == "dry_run"
    assert result["conversions_ready"] == 2
    assert result["skipped"] == {"no_gclid": 1, "below_min_score": 1, "duplicate_gclid": 0}
    assert client.calls == 0


def test_live_run_uploads_every_ready_conversion(tmp_path):
    result, client, _ = run(tmp_path, live=True)
    assert result["status"] == "uploaded"
    assert result["uploaded"] == 2
    assert [c["gclid"] for c in client.uploaded] == ["G1", "G2"]


def test_kill_switch_stops_the_run_before_anything_happens(tmp_path):
    result, client, log_path = run(tmp_path, live=True, env={"PIPELINE_ENABLED": "0"})
    assert result["status"] == "disabled"
    assert "leads_read" not in result
    assert client.calls == 0
    assert read_log(log_path)[0]["status"] == "disabled"


def test_temporary_rate_limits_are_survived(tmp_path):
    waits = []
    result, client, _ = run(
        tmp_path, client=FakeAdsClient(fail_first_calls=2), live=True, sleep=waits.append
    )
    assert result["status"] == "uploaded"
    assert waits == [1.0, 2.0]


def test_endless_rate_limits_end_in_a_logged_failure_not_a_crash(tmp_path):
    result, client, log_path = run(tmp_path, client=FakeAdsClient(fail_first_calls=99), live=True)
    assert result["status"] == "failed"
    assert "rate limits" in result["error"]
    assert read_log(log_path)[0]["status"] == "failed"


def test_a_bad_data_file_is_a_logged_failure_with_the_line_number(tmp_path):
    bad_file = write_csv(tmp_path / "bad.csv", [make_row(), make_row(lead_id="L2", call_seconds="x")])
    log_path = tmp_path / "run_log.jsonl"
    result = run_pipeline(bad_file, FakeAdsClient(), log_path, env={}, now=fixed_clock)
    assert result["status"] == "failed"
    assert "Line 3" in result["error"]


def test_a_missing_data_file_is_a_logged_failure(tmp_path):
    log_path = tmp_path / "run_log.jsonl"
    result = run_pipeline(tmp_path / "nope.csv", FakeAdsClient(), log_path, env={}, now=fixed_clock)
    assert result["status"] == "failed"


def test_every_run_adds_one_line_to_the_log(tmp_path):
    log_path = tmp_path / "logs" / "run_log.jsonl"
    leads_file = sample_leads_file(tmp_path)
    for _ in range(3):
        run_pipeline(leads_file, FakeAdsClient(), log_path, env={}, now=fixed_clock)
    entries = read_log(log_path)
    assert len(entries) == 3
    assert entries[0]["timestamp"] == "2026-03-10T08:00:00+00:00"


def test_live_run_with_nothing_to_report_uploads_nothing(tmp_path):
    result, client, _ = run(tmp_path, live=True, min_score=101)
    assert result["status"] == "nothing_to_upload"
    assert client.calls == 0


def test_conversions_can_be_written_to_a_file(tmp_path):
    output = tmp_path / "output" / "conversions.json"
    run(tmp_path, output_path=output)
    written = json.loads(output.read_text())
    assert [c["gclid"] for c in written] == ["G1", "G2"]
