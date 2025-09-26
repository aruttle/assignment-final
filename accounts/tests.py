from __future__ import annotations

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

User = get_user_model()


class AuthFlowTests(TestCase):
    def test_signup_page_loads(self):
        resp = self.client.get(reverse("accounts:signup"))
        self.assertEqual(resp.status_code, 200)

    def test_login_and_password_reset(self):
        # Create a user and verify login works
        User.objects.create_user(username="alice", email="alice@example.com", password="secret12345")

        login_resp = self.client.post(reverse("login"), {
            "username": "alice",
            "password": "secret12345",
        })
        # Built-in login redirects on success
        self.assertIn(login_resp.status_code, (302, 303))

        # Password reset sends email
        resp = self.client.post(reverse("password_reset"), {"email": "alice@example.com"})
        self.assertIn(resp.status_code, (302, 303))  # redirects to done
        self.assertGreaterEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/reset/", mail.outbox[-1].body)
