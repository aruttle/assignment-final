# core/management/commands/seed_demo.py
from __future__ import annotations
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Spot
from activities.models import Provider, Activity, Booking
from buddies.models import BuddySession

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Clear demo data first")

    def handle(self, *args, **opts):
        if opts["reset"]:
            self.stdout.write("Clearing existing demo data…")
            Booking.objects.all().delete()
            Activity.objects.all().delete()
            Provider.objects.all().delete()
            BuddySession.objects.all().delete()
            Spot.objects.all().delete()

        # Demo user
        user, _ = User.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@example.com"}
        )
        if not user.has_usable_password():
            user.set_password("demo12345")
            user.save()

        # Spots
        spots = [
            ("Kilrush Marina", 52.6406, -9.4881, "kayak"),
            ("Scattery Ferry Slip", 52.6197, -9.5149, "swim"),
            ("Foynes Slipway", 52.6128, -9.1087, "kayak"),
            ("Shannon Airport Wetlands", 52.7000, -8.9140, "hike"),
        ]
        created_spots = []
        for name, lat, lon, typ in spots:
            s, _ = Spot.objects.get_or_create(name=name, defaults={"lat": lat, "lon": lon, "type": typ})
            created_spots.append(s)

        # Provider & Activities
        prov, _ = Provider.objects.get_or_create(
            name="SEA Adventures",
            defaults={"contact_email": "hello@sea.local"}
        )
        act1, _ = Activity.objects.get_or_create(
            provider=prov,
            title="Kayak Intro",
            defaults={"description": "Guided paddle on the estuary",
                      "price": 45, "duration_minutes": 90, "capacity": 6}
        )
        act2, _ = Activity.objects.get_or_create(
            provider=prov,
            title="Sunset Swim",
            defaults={"description": "Group dip with guide",
                      "price": 15, "duration_minutes": 60, "capacity": 12}
        )

        # Buddy session (owner field may vary: creator/created_by/host/owner/user)
        owner_field = {f.name for f in BuddySession._meta.get_fields()} \
            .intersection({"creator", "created_by", "host", "owner", "user"})
        owner_kw = {}
        if owner_field:
            owner_kw[next(iter(owner_field))] = user

        start = timezone.now() + timezone.timedelta(hours=6)
        sess, _ = BuddySession.objects.get_or_create(
            title="Evening Dip",
            defaults={
                "type": "swim",
                "start_dt": start,
                "lat": created_spots[1].lat if created_spots else 52.62,
                "lon": created_spots[1].lon if created_spots else -9.51,
                "location_name": created_spots[1].name if created_spots else "Scattery Slip",
                "capacity": 10,
                **owner_kw,
            },
        )
        sess.participants.add(user)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("Login with: demo / demo12345 (non-staff)")
