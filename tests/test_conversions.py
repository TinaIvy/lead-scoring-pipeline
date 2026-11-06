from helpers import make_lead

from lead_pipeline.conversions import build_conversions

GOOD = {"call_seconds": 300, "appointment_booked": True, "appointment_attended": True}  # 80 points


def test_a_good_lead_becomes_a_conversion():
    batch = build_conversions([make_lead(gclid="G1", **GOOD)])
    assert len(batch.conversions) == 1
    assert batch.skipped == {"no_gclid": 0, "below_min_score": 0, "duplicate_gclid": 0}


def test_conversion_has_the_fields_the_platform_needs():
    lead = make_lead(gclid="G1", created_date="2026-03-05", **GOOD)
    conversion = build_conversions([lead]).conversions[0]
    assert conversion == {
        "gclid": "G1",
        "conversion_action": "lead_quality_high",
        "conversion_date_time": "2026-03-05 12:00:00+00:00",
        "conversion_value": 80.0,
        "currency_code": "USD",
    }


def test_leads_without_a_click_id_are_skipped():
    batch = build_conversions([make_lead(gclid="", **GOOD)])
    assert batch.conversions == []
    assert batch.skipped["no_gclid"] == 1


def test_leads_below_the_minimum_score_are_skipped():
    batch = build_conversions([make_lead(gclid="G1", call_seconds=130)])  # 20 points
    assert batch.conversions == []
    assert batch.skipped["below_min_score"] == 1


def test_a_lead_exactly_at_the_minimum_score_is_included():
    lead = make_lead(gclid="G1", call_seconds=130, appointment_booked=True)  # 45 points
    assert len(build_conversions([lead], min_score=45).conversions) == 1
    assert len(build_conversions([lead], min_score=46).conversions) == 0


def test_a_click_is_reported_once_and_the_higher_score_wins():
    weaker = make_lead(lead_id="L1", gclid="SAME", call_seconds=130, appointment_booked=True)  # 45
    stronger = make_lead(lead_id="L2", gclid="SAME", **GOOD)  # 80
    for leads in ([weaker, stronger], [stronger, weaker]):
        batch = build_conversions(leads)
        assert [c["conversion_value"] for c in batch.conversions] == [80.0]
        assert batch.skipped["duplicate_gclid"] == 1


def test_medium_leads_get_a_medium_action():
    lead = make_lead(gclid="G1", call_seconds=130, appointment_booked=True)
    assert build_conversions([lead]).conversions[0]["conversion_action"] == "lead_quality_medium"


def test_no_leads_means_no_conversions():
    batch = build_conversions([])
    assert batch.conversions == []
