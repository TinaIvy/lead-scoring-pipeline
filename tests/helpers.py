"""Small helpers shared by the tests."""

import csv

from lead_pipeline.models import Lead

CSV_COLUMNS = [
    "lead_id",
    "created_date",
    "source",
    "gclid",
    "call_seconds",
    "appointment_booked",
    "appointment_attended",
    "payment_amount",
]


def make_lead(**overrides):
    """Build a Lead with boring defaults, changing only what a test cares about."""
    values = {
        "lead_id": "L1",
        "created_date": "2026-03-01",
        "source": "google_search",
        "gclid": "G1",
        "call_seconds": 0,
        "appointment_booked": False,
        "appointment_attended": False,
        "payment_amount": 0.0,
    }
    values.update(overrides)
    return Lead(**values)


def make_row(**overrides):
    """Build one CSV row (all text), changing only what a test cares about."""
    row = {
        "lead_id": "L1",
        "created_date": "2026-03-01",
        "source": "google_search",
        "gclid": "G1",
        "call_seconds": "100",
        "appointment_booked": "0",
        "appointment_attended": "0",
        "payment_amount": "0",
    }
    row.update(overrides)
    return row


def write_csv(path, rows, columns=CSV_COLUMNS):
    """Write rows to a CSV file and return the path."""
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path
