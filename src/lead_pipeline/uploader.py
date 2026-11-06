"""Send conversions to the ad platform, retrying when it says "slow down".

There is no real network code in this project. `FakeAdsClient` stands in for
the real API so the retry logic can be shown and tested safely.
"""

import time


class RateLimitError(Exception):
    """The platform asked us to slow down."""


class FakeAdsClient:
    """A pretend ad platform. It never touches the network.

    `fail_first_calls` makes the first few uploads fail with a rate limit
    error, to show what the retry logic does.
    """

    def __init__(self, fail_first_calls=0):
        self._failures_left = fail_first_calls
        self.calls = 0
        self.uploaded = []

    def upload_conversions(self, conversions):
        self.calls += 1
        if self._failures_left > 0:
            self._failures_left -= 1
            raise RateLimitError("simulated rate limit")
        self.uploaded.extend(conversions)
        return len(conversions)


def upload_with_retry(client, conversions, max_attempts=4, base_delay=1.0, sleep=time.sleep):
    """Upload, waiting longer after each rate limit error (1s, 2s, 4s, ...).

    Gives up by raising the last RateLimitError once `max_attempts` is used up.
    Any other kind of error is not retried, because retrying a real bug only
    repeats it. `sleep` can be replaced in tests so they run instantly.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return client.upload_conversions(conversions)
        except RateLimitError:
            if attempt == max_attempts:
                raise
            sleep(base_delay * 2 ** (attempt - 1))
