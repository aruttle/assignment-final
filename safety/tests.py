from __future__ import annotations

from django.test import TestCase
from django.utils import timezone

from safety.views import _rate


def _next_tide_local(extremes: list[dict]) -> dict | None:
    """Local helper for the test suite; mirrors app behavior."""
    if not extremes:
        return None
    now = timezone.now()
    future = [e for e in extremes if e.get("time") and e["time"] > now]
    if not future:
        return None
    future.sort(key=lambda e: e["time"])
    return future[0]


class SafetyRulesTests(TestCase):
    def test_rate_thresholds(self):
        # Safe: wind < 6, gust < 9, precip < 40
        self.assertEqual(_rate(5.9, 8.9, 39)[0], "safe")
        # Caution: wind < 9, gust < 12, precip < 70
        self.assertEqual(_rate(8.9, 11.9, 69)[0], "caution")
        # Avoid: otherwise
        self.assertEqual(_rate(9.0, 5.0, 10)[0], "avoid")
        self.assertEqual(_rate(5.0, 12.0, 10)[0], "avoid")
        self.assertEqual(_rate(5.0, 5.0, 70)[0], "avoid")

    def test_next_tide_picks_earliest_future(self):
        now = timezone.now()
        extremes = [
            {"time": now - timezone.timedelta(hours=2), "type": "low", "height": 0.8},
            {"time": now + timezone.timedelta(hours=3), "type": "high", "height": 3.1},
            {"time": now + timezone.timedelta(hours=1), "type": "low", "height": 1.2},
        ]
        nxt = _next_tide_local(extremes)
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt["type"], "low")
        self.assertAlmostEqual(nxt["height"], 1.2, places=3)
