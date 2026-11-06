"""Turn what we know about a lead into a quality score from 0 to 100.

The score rewards progress that is hard to fake: a long conversation, a booked
appointment, a shown-up appointment, and money paid. Each part is a separate,
visible rule so the score can be explained and adjusted.

    Call length        up to 30 points
    Appointment booked 25 points
    Appointment kept   25 points
    Payment            up to 20 points
"""

# (minimum seconds, points), checked from the longest call down.
CALL_POINTS = ((300, 30), (120, 20), (30, 10))
BOOKED_POINTS = 25
ATTENDED_POINTS = 25
SMALL_PAYMENT_POINTS = 10
LARGE_PAYMENT_POINTS = 20
LARGE_PAYMENT_THRESHOLD = 500

HIGH_TIER_MIN = 70
MEDIUM_TIER_MIN = 40


def call_points(call_seconds):
    for minimum_seconds, points in CALL_POINTS:
        if call_seconds >= minimum_seconds:
            return points
    return 0


def payment_points(payment_amount):
    if payment_amount >= LARGE_PAYMENT_THRESHOLD:
        return LARGE_PAYMENT_POINTS
    if payment_amount > 0:
        return SMALL_PAYMENT_POINTS
    return 0


def score_lead(lead):
    """Return a whole-number score from 0 to 100."""
    score = call_points(lead.call_seconds) + payment_points(lead.payment_amount)
    if lead.appointment_booked:
        score += BOOKED_POINTS
    if lead.appointment_attended:
        score += ATTENDED_POINTS
    return score


def quality_tier(score):
    """Group a score into "high", "medium" or "low"."""
    if score >= HIGH_TIER_MIN:
        return "high"
    if score >= MEDIUM_TIER_MIN:
        return "medium"
    return "low"
