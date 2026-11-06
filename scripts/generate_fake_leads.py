"""Generate the made-up leads in data/leads.csv.

Run from the project folder:  python scripts/generate_fake_leads.py

The random seed is fixed, so the file comes out the same every time. Nothing
here comes from a real business: names, click ids and amounts are all invented.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
LEAD_COUNT = 80
START_DATE = date(2026, 3, 1)
OUTPUT = Path("data/leads.csv")

SOURCES = ["google_search", "performance_max", "local_services", "meta", "organic"]
SOURCE_WEIGHTS = [35, 25, 15, 15, 10]
SOURCES_WITH_GCLID = {"google_search", "performance_max"}
PAYMENT_CHOICES = [250, 500, 750, 1200, 2400]


def make_lead(rng, number):
    source = rng.choices(SOURCES, weights=SOURCE_WEIGHTS)[0]
    interest = rng.random()  # hidden "how interested is this person", from 0 to 1

    call_seconds = max(5, int(rng.gauss(60 + 300 * interest, 40)))
    booked = interest + rng.uniform(-0.2, 0.2) > 0.45
    attended = booked and rng.random() < 0.55 + 0.3 * interest
    paid = attended and rng.random() < 0.7
    payment = rng.choice(PAYMENT_CHOICES) if paid else 0

    # Some Google clicks arrive without a click id (for example, tracking was blocked).
    has_gclid = source in SOURCES_WITH_GCLID and rng.random() > 0.05
    return {
        "lead_id": f"L{number:04d}",
        "created_date": (START_DATE + timedelta(days=rng.randrange(30))).isoformat(),
        "source": source,
        "gclid": f"FAKE-GCLID-{number:04d}" if has_gclid else "",
        "call_seconds": call_seconds,
        "appointment_booked": int(booked),
        "appointment_attended": int(attended),
        "payment_amount": payment,
    }


def main():
    rng = random.Random(SEED)
    leads = [make_lead(rng, number) for number in range(1, LEAD_COUNT + 1)]

    # Three repeat leads that came from the same click, to exercise de-duplication.
    # They are copies of good leads, so both copies are worth reporting and the
    # pipeline has to choose between them.
    good_clicks = [
        lead
        for lead in leads
        if lead["gclid"] and lead["appointment_booked"] and lead["call_seconds"] >= 120
    ]
    for offset, original in enumerate(rng.sample(good_clicks, 3), start=1):
        repeat = dict(original)
        repeat["lead_id"] = f"L{LEAD_COUNT + offset:04d}"
        repeat["call_seconds"] = max(5, int(original["call_seconds"] * rng.uniform(0.3, 1.2)))
        leads.append(repeat)

    leads.sort(key=lambda lead: (lead["created_date"], lead["lead_id"]))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(leads[0]))
        writer.writeheader()
        writer.writerows(leads)
    print(f"Wrote {len(leads)} made-up leads to {OUTPUT}")


if __name__ == "__main__":
    main()
