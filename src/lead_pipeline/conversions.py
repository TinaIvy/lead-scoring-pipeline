"""Build the conversion records we would send back to the ad platform.

An "offline conversion" tells an ad platform: "the click with this ID later
turned into a lead worth this much". Bidding then learns to find more people
like that. Only leads that came from an ad click (they have a gclid) can be
reported, and only the good ones are worth reporting.
"""

from dataclasses import dataclass

from .scoring import quality_tier, score_lead

DEFAULT_MIN_SCORE = 40
CONVERSION_TIME_OF_DAY = "12:00:00+00:00"  # the sample data has dates only


@dataclass
class ConversionBatch:
    conversions: list  # ready-to-send dictionaries
    skipped: dict  # how many leads were left out, and why


def _to_conversion(lead, score):
    return {
        "gclid": lead.gclid,
        "conversion_action": f"lead_quality_{quality_tier(score)}",
        "conversion_date_time": f"{lead.created_date} {CONVERSION_TIME_OF_DAY}",
        "conversion_value": float(score),
        "currency_code": "USD",
    }


def build_conversions(leads, min_score=DEFAULT_MIN_SCORE):
    """Choose which leads to report and build their conversion records.

    Leads are skipped when they have no click id, score below `min_score`, or
    share a click id with a better-scoring lead. A click can only be reported
    once, so for repeats the highest score wins.
    """
    skipped = {"no_gclid": 0, "below_min_score": 0, "duplicate_gclid": 0}
    best_by_gclid = {}  # gclid -> (score, lead)

    for lead in leads:
        if not lead.gclid:
            skipped["no_gclid"] += 1
            continue
        score = score_lead(lead)
        if score < min_score:
            skipped["below_min_score"] += 1
            continue
        existing = best_by_gclid.get(lead.gclid)
        if existing is None:
            best_by_gclid[lead.gclid] = (score, lead)
            continue
        skipped["duplicate_gclid"] += 1
        if score > existing[0]:
            best_by_gclid[lead.gclid] = (score, lead)

    conversions = [_to_conversion(lead, score) for score, lead in best_by_gclid.values()]
    return ConversionBatch(conversions=conversions, skipped=skipped)
