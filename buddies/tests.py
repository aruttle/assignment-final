from __future__ import annotations

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from buddies.models import BuddySession

User = get_user_model()


def _first_present(model, candidates: list[str]) -> str | None:
    names = {f.name for f in model._meta.get_fields()}
    for c in candidates:
        if c in names:
            return c
    return None


class DashboardSmokeTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username="host", email="h@example.com", password="pw12345")
        self.u2 = User.objects.create_user(username="joiner", email="j@example.com", password="pw12345")

        owner_field = _first_present(BuddySession, ["creator", "created_by", "host", "owner", "user"])
        owner_kw = {owner_field: self.u1} if owner_field else {}

        # Create a future session with required owner at create-time
        self.session = BuddySession.objects.create(
            title="Morning Dip",
            type="swim",
            start_dt=timezone.now() + timezone.timedelta(hours=2),
            lat=52.7, lon=-8.8, location_name="Test Pier",
            capacity=8,
            **owner_kw,
        )
        # Add a participant (u2)
        self.session.participants.add(self.u2)

    def test_me_dashboard_requires_login(self):
        resp = self.client.get("/me/")
        self.assertIn(resp.status_code, (302, 301))  # redirected to login

    def test_me_dashboard_lists_sessions_when_logged_in(self):
        self.client.login(username="host", password="pw12345")
        resp = self.client.get("/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Morning Dip")
