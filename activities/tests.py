# activities/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, date, time as dtime

from .models import Provider, Activity, Booking

User = get_user_model()

def aware_at(a_date: date, hour: int):
    """Helper: aware datetime at given local date + hour:00."""
    naive = datetime.combine(a_date, dtime(hour=hour, minute=0))
    tz = timezone.get_current_timezone()
    return timezone.make_aware(naive, tz)

class AvailabilityAndBookingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.provider = Provider.objects.create(name="SEA Tours", contact_email="tours@example.com")
        self.activity = Activity.objects.create(
            provider=self.provider,
            title="Kayak Intro",
            description="Fun on the estuary",
            price=45,
            duration_minutes=90,
            capacity=3,  
        )
        self.user = User.objects.create_user(username="alan", password="testpass123")
        self.today = timezone.localdate()

    def test_availability_lists_slots(self):
        """GET availability should include expected slot labels (e.g., 09:00) when not full."""
        url = reverse("activities:availability", args=[self.activity.id])
        resp = self.client.get(url, {"date": self.today.isoformat()}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        # Our slot hours are 9,11,13,15; check at least one appears
        self.assertIn("09:00", resp.content.decode())

    def test_availability_excludes_full_slot(self):
        """If a slot reaches capacity, it should not be listed."""
        slot_dt = aware_at(self.today, 9)
        # Fill capacity with one booking for party_size=3
        Booking.objects.create(
            user=self.user, activity=self.activity, start_dt=slot_dt, party_size=3, status="confirmed"
        )
        url = reverse("activities:availability", args=[self.activity.id])
        resp = self.client.get(url, {"date": self.today.isoformat()}, HTTP_HX_REQUEST="true")
        html = resp.content.decode()
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("09:00", html)  # fully booked slot should be hidden
        self.assertIn("11:00", html)     # other slots remain

    def test_booking_requires_login_hx_redirect(self):
        """Unauthenticated POST should return HX-Redirect header to login."""
        slot_dt = aware_at(self.today, 11)
        url = reverse("activities:book", args=[self.activity.id])
        resp = self.client.post(
            url,
            {"start_dt": slot_dt.isoformat(), "party_size": 1},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("HX-Redirect", resp.headers)
        # sanity: redirect points to admin login (I'll add auth later)
        self.assertIn("/admin/login/", resp.headers["HX-Redirect"])

    def test_booking_creates_when_authenticated(self):
        """Authenticated POST should create a booking and return confirmation panel."""
        self.client.login(username="alan", password="testpass123")
        slot_dt = aware_at(self.today, 13)
        url = reverse("activities:book", args=[self.activity.id])
        resp = self.client.post(
            url,
            {"start_dt": slot_dt.isoformat(), "party_size": 2},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("Booking confirmed", html)
        self.assertEqual(Booking.objects.count(), 1)
        b = Booking.objects.first()
        self.assertEqual(b.party_size, 2)
        self.assertEqual(b.start_dt, slot_dt)
        self.assertEqual(b.status, "confirmed")

    def test_booking_rejects_over_capacity(self):
        """If remaining seats are fewer than requested, return inline error."""
        # Pre-fill 2 seats at 15:00
        self.client.login(username="alan", password="testpass123")
        slot_dt = aware_at(self.today, 15)
        Booking.objects.create(
            user=self.user, activity=self.activity, start_dt=slot_dt, party_size=2, status="confirmed"
        )
        # Try to book 2 more (capacity is 3 → only 1 left)
        url = reverse("activities:book", args=[self.activity.id])
        resp = self.client.post(
            url,
            {"start_dt": slot_dt.isoformat(), "party_size": 2},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("Only 1 seats left", html)  # inline error message
        # No new booking created
        self.assertEqual(Booking.objects.count(), 1)
