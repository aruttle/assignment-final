from django.core.management.base import BaseCommand
from activities.models import Provider, Activity

class Command(BaseCommand):
    help = "Seed demo providers and activities for SEA"

    def handle(self, *args, **options):
        data = [
            {
                "provider": {"name": "SEA Tours", "contact_email": "tours@example.com"},
                "activities": [
                    {"title": "Kayak Intro", "description": "Gentle paddle session.", "price": 45, "duration_minutes": 90, "capacity": 8},
                    {"title": "Estuary Kayak Tour", "description": "2h guided tour.", "price": 65, "duration_minutes": 120, "capacity": 10},
                ],
            },
            {
                "provider": {"name": "Shannon Yoga", "contact_email": "yoga@example.com"},
                "activities": [
                    {"title": "Sunrise Yoga (Pier)", "description": "60 min vinyasa.", "price": 15, "duration_minutes": 60, "capacity": 20},
                ],
            },
            {
                "provider": {"name": "Sauna on Wheels", "contact_email": "sauna@example.com"},
                "activities": [
                    {"title": "Mobile Sauna Session", "description": "45 min hot/cold.", "price": 20, "duration_minutes": 45, "capacity": 6},
                ],
            },
        ]

        created_p = 0
        created_a = 0
        for block in data:
            p_info = block["provider"]
            provider, p_created = Provider.objects.get_or_create(
                name=p_info["name"], defaults={"contact_email": p_info["contact_email"]}
            )
            created_p += int(p_created)
            for a in block["activities"]:
                _, a_created = Activity.objects.get_or_create(
                    provider=provider, title=a["title"],
                    defaults={
                        "description": a["description"],
                        "price": a["price"],
                        "duration_minutes": a["duration_minutes"],
                        "capacity": a["capacity"],
                    }
                )
                created_a += int(a_created)

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: providers +{created_p}, activities +{created_a}"
        ))
