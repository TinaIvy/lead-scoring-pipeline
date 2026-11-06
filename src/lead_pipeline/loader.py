"""Read leads from a CSV file and check that the data makes sense.

Bad data is rejected loudly, with the line number, instead of being scored
anyway. A wrong number sent back to an ad platform quietly teaches its
bidding the wrong lesson.
"""

import csv
from datetime import date

from .models import Lead

REQUIRED_COLUMNS = (
    "lead_id",
    "created_date",
    "source",
    "gclid",
    "call_seconds",
    "appointment_booked",
    "appointment_attended",
    "payment_amount",
)


def _parse_flag(value, field, line):
    if value not in ("0", "1"):
        raise ValueError(f"Line {line}: {field} must be 0 or 1, got {value!r}")
    return value == "1"


def parse_lead(row, line):
    """Turn one CSV row (a dictionary of text) into a validated Lead."""
    try:
        date.fromisoformat(row["created_date"])
    except ValueError:
        raise ValueError(
            f"Line {line}: created_date must look like 2026-03-15, got {row['created_date']!r}"
        ) from None

    try:
        call_seconds = int(row["call_seconds"])
        payment_amount = float(row["payment_amount"])
    except ValueError:
        raise ValueError(f"Line {line}: call_seconds and payment_amount must be numbers") from None
    if call_seconds < 0 or payment_amount < 0:
        raise ValueError(f"Line {line}: call_seconds and payment_amount cannot be negative")

    booked = _parse_flag(row["appointment_booked"], "appointment_booked", line)
    attended = _parse_flag(row["appointment_attended"], "appointment_attended", line)
    if attended and not booked:
        raise ValueError(f"Line {line}: an appointment was attended but never booked")

    return Lead(
        lead_id=row["lead_id"].strip(),
        created_date=row["created_date"],
        source=row["source"].strip(),
        gclid=row["gclid"].strip(),
        call_seconds=call_seconds,
        appointment_booked=booked,
        appointment_attended=attended,
        payment_amount=payment_amount,
    )


def load_leads(path):
    """Read a CSV file and return a list of Lead objects."""
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"The CSV file is missing columns: {', '.join(missing)}")

        leads = []
        seen_ids = set()
        for line, row in enumerate(reader, start=2):  # line 1 is the header
            lead = parse_lead(row, line)
            if lead.lead_id in seen_ids:
                raise ValueError(f"Line {line}: lead_id {lead.lead_id!r} appears twice")
            seen_ids.add(lead.lead_id)
            leads.append(lead)
    return leads
