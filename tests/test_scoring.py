import pytest
from helpers import make_lead

from lead_pipeline.scoring import call_points, payment_points, quality_tier, score_lead


@pytest.mark.parametrize(
    "seconds, expected",
    [(0, 0), (29, 0), (30, 10), (119, 10), (120, 20), (299, 20), (300, 30), (900, 30)],
)
def test_call_points_step_up_at_each_threshold(seconds, expected):
    assert call_points(seconds) == expected


@pytest.mark.parametrize(
    "amount, expected",
    [(0, 0), (1, 10), (499.99, 10), (500, 20), (2400, 20)],
)
def test_payment_points_step_up_at_each_threshold(amount, expected):
    assert payment_points(amount) == expected


def test_a_lead_with_no_progress_scores_zero():
    assert score_lead(make_lead()) == 0


def test_booking_adds_25_points():
    assert score_lead(make_lead(appointment_booked=True)) == 25


def test_attending_adds_another_25_points():
    lead = make_lead(appointment_booked=True, appointment_attended=True)
    assert score_lead(lead) == 50


def test_the_best_possible_lead_scores_100():
    lead = make_lead(
        call_seconds=600,
        appointment_booked=True,
        appointment_attended=True,
        payment_amount=1200,
    )
    assert score_lead(lead) == 100


def test_scores_stay_between_0_and_100_for_extreme_values():
    huge = make_lead(
        call_seconds=10**9,
        appointment_booked=True,
        appointment_attended=True,
        payment_amount=10**9,
    )
    assert 0 <= score_lead(make_lead()) <= score_lead(huge) <= 100


@pytest.mark.parametrize(
    "score, tier",
    [(100, "high"), (70, "high"), (69, "medium"), (40, "medium"), (39, "low"), (0, "low")],
)
def test_tiers_change_at_the_right_scores(score, tier):
    assert quality_tier(score) == tier
