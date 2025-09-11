from django.core.management.base import BaseCommand
from core.models import Spot

SPOTS = [
    {"name": "Bunratty Pier", "lat": 52.699, "lon": -8.814, "type": "kayak"},
    {"name": "Kilrush Marina", "lat": 52.640, "lon": -9.483, "type": "kayak"},
    {"name": "Cappa Pier", "lat": 52.638, "lon": -9.506, "type": "swim"},
]

class Command(BaseCommand):
    help = "Seed initial Shannon Estuary spots"

    def handle(self, *args, **kwargs):
        created = 0
        for s in SPOTS:
            obj, was_created = Spot.objects.get_or_create(
                name=s["name"],
                defaults={
                    "type": s["type"],
                    "lat": s["lat"],
                    "lon": s["lon"],
                    "is_active": True
                }
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: +{created} new spots (total: {Spot.objects.count()})"
        ))
