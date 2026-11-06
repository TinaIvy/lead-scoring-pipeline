"""The one data type the pipeline passes around."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Lead:
    """One lead, with what we know about how it progressed."""

    lead_id: str
    created_date: str  # YYYY-MM-DD
    source: str  # for example "google_search" or "meta"
    gclid: str  # click id from a Google ad; empty when the lead did not come from a click
    call_seconds: int  # length of the longest call with this lead
    appointment_booked: bool
    appointment_attended: bool
    payment_amount: float  # 0 when nothing was paid
