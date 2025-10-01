from django.db import models

SPOT_TYPES = [
    ("kayak", "Kayak"),
    ("swim", "Swim"),
    ("hike", "Hike"),
    ("cycle", "Cycle"),
    ("sup", "Stand Up Paddle"),
    ("sailing", "Sailing"),
    ("yoga", "Yoga"),
    ("sauna", "Mobile Sauna"),
    ("tour", "Tour"),
    ("tri", "Triathlon"),
]

class Spot(models.Model):
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=20, choices=SPOT_TYPES, blank=True, default="")
    lat = models.DecimalField(max_digits=8, decimal_places=5)
    lon = models.DecimalField(max_digits=8, decimal_places=5)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
