import pytest
from helpers import CSV_COLUMNS, make_row, write_csv

from lead_pipeline.loader import load_leads


def test_loads_a_valid_file(tmp_path):
    path = write_csv(
        tmp_path / "leads.csv",
        [make_row(call_seconds="250", appointment_booked="1", payment_amount="500.50")],
    )
    leads = load_leads(path)
    assert len(leads) == 1
    lead = leads[0]
    assert lead.lead_id == "L1"
    assert lead.call_seconds == 250
    assert lead.appointment_booked is True
    assert lead.appointment_attended is False
    assert lead.payment_amount == 500.50


def test_an_empty_click_id_is_allowed(tmp_path):
    path = write_csv(tmp_path / "leads.csv", [make_row(gclid="")])
    assert load_leads(path)[0].gclid == ""


def test_missing_column_is_reported_by_name(tmp_path):
    columns = [c for c in CSV_COLUMNS if c != "gclid"]
    path = write_csv(tmp_path / "leads.csv", [make_row()], columns=columns)
    with pytest.raises(ValueError, match="gclid"):
        load_leads(path)


def test_bad_date_is_reported_with_its_line_number(tmp_path):
    path = write_csv(tmp_path / "leads.csv", [make_row(), make_row(lead_id="L2", created_date="03/05/2026")])
    with pytest.raises(ValueError, match="Line 3"):
        load_leads(path)


def test_attended_without_booked_is_rejected(tmp_path):
    path = write_csv(tmp_path / "leads.csv", [make_row(appointment_attended="1")])
    with pytest.raises(ValueError, match="never booked"):
        load_leads(path)


def test_duplicate_lead_ids_are_rejected(tmp_path):
    path = write_csv(tmp_path / "leads.csv", [make_row(), make_row()])
    with pytest.raises(ValueError, match="twice"):
        load_leads(path)


def test_negative_payment_is_rejected(tmp_path):
    path = write_csv(tmp_path / "leads.csv", [make_row(payment_amount="-5")])
    with pytest.raises(ValueError, match="negative"):
        load_leads(path)


def test_non_numeric_call_length_is_rejected(tmp_path):
    path = write_csv(tmp_path / "leads.csv", [make_row(call_seconds="long")])
    with pytest.raises(ValueError, match="numbers"):
        load_leads(path)


def test_flags_must_be_zero_or_one(tmp_path):
    path = write_csv(tmp_path / "leads.csv", [make_row(appointment_booked="yes")])
    with pytest.raises(ValueError, match="must be 0 or 1"):
        load_leads(path)
