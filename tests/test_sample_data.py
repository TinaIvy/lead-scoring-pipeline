"""Checks on the made-up data file that ships with the project."""

from lead_pipeline.conversions import build_conversions
from lead_pipeline.loader import load_leads

LEADS_FILE = "data/leads.csv"


def test_the_sample_file_loads_cleanly():
    leads = load_leads(LEADS_FILE)
    assert len(leads) == 83


def test_the_sample_file_exercises_every_skip_reason():
    batch = build_conversions(load_leads(LEADS_FILE))
    assert batch.conversions
    assert all(count > 0 for count in batch.skipped.values())


def test_every_reported_click_id_is_unique():
    gclids = [c["gclid"] for c in build_conversions(load_leads(LEADS_FILE)).conversions]
    assert len(gclids) == len(set(gclids))


def test_the_sample_file_contains_no_real_click_ids():
    assert all(
        lead.gclid.startswith("FAKE-GCLID-") for lead in load_leads(LEADS_FILE) if lead.gclid
    )
