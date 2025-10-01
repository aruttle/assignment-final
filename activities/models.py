from django.db import models
from django.conf import settings
from django.db.models import Q


class Provider(models.Model):
    name = models.CharField(max_length=120)
    contact_email = models.EmailField(blank=True, default="")

    def __str__(self):
        return self.name


class Activity(models.Model):
    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="activities"
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    duration_minutes = models.PositiveIntegerField(default=60)
    capacity = models.PositiveIntegerField(default=8)
    created_at = models.DateTimeField(auto_now_add=True)

    # Cover image for cards/headers
    image = models.ImageField(upload_to="activities/covers/", blank=True, null=True)

    # Allow activities that don’t need booking 
    requires_booking = models.BooleanField(
        default=True,
        help_text="If off, no slots/booking are shown; page is informational only.",
    )

    spot = models.ForeignKey(
        "core.Spot",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activities",
        help_text="Where this activity happens.",
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} — {self.provider.name}"

    @property
    def cover_image_url(self) -> str:
        try:
            return self.image.url  
        except Exception:
            return ""

    @property
    def is_free(self) -> bool:
        try:
            return float(self.price) == 0
        except Exception:
            return False


STATUS_CHOICES = [
    ("confirmed", "Confirmed"),
    ("cancelled", "Cancelled"),
]


class Booking(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="bookings"
    )
    start_dt = models.DateTimeField()
    party_size = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default="confirmed"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["start_dt"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "activity", "start_dt"],
                condition=Q(status="confirmed"),
                name="uniq_confirmed_booking_per_user_slot",
            )
        ]

    def __str__(self):
        return f"{self.activity.title} @ {self.start_dt:%Y-%m-%d %H:%M} ({self.party_size})"
