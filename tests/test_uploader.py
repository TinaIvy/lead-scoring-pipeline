import pytest

from lead_pipeline.uploader import FakeAdsClient, RateLimitError, upload_with_retry

CONVERSIONS = [{"gclid": "G1"}, {"gclid": "G2"}]


def test_upload_that_works_first_time_never_waits():
    waits = []
    client = FakeAdsClient()
    assert upload_with_retry(client, CONVERSIONS, sleep=waits.append) == 2
    assert waits == []
    assert client.calls == 1


def test_rate_limits_are_retried_with_doubling_waits():
    waits = []
    client = FakeAdsClient(fail_first_calls=2)
    assert upload_with_retry(client, CONVERSIONS, sleep=waits.append) == 2
    assert waits == [1.0, 2.0]
    assert client.calls == 3
    assert client.uploaded == CONVERSIONS


def test_base_delay_sets_the_first_wait():
    waits = []
    client = FakeAdsClient(fail_first_calls=2)
    upload_with_retry(client, CONVERSIONS, base_delay=0.5, sleep=waits.append)
    assert waits == [0.5, 1.0]


def test_gives_up_after_the_last_attempt():
    waits = []
    client = FakeAdsClient(fail_first_calls=10)
    with pytest.raises(RateLimitError):
        upload_with_retry(client, CONVERSIONS, max_attempts=4, sleep=waits.append)
    assert client.calls == 4
    assert waits == [1.0, 2.0, 4.0]  # no wait after the final failure
    assert client.uploaded == []


def test_other_errors_are_not_retried():
    class BrokenClient:
        calls = 0

        def upload_conversions(self, conversions):
            self.calls += 1
            raise ValueError("bad payload")

    client = BrokenClient()
    with pytest.raises(ValueError):
        upload_with_retry(client, CONVERSIONS, sleep=lambda seconds: None)
    assert client.calls == 1
