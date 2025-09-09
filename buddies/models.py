from django.conf import settings
from django.db import models

SESSION_TYPES = [
    ("swim", "Swim"),
    ("kayak", "Kayak"),
    ("hike", "Hike"),
    ("cycle", "Cycle"),
]

class BuddySession(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_buddy_sessions")
    title = models.CharField(max_length=140)
    type = models.CharField(max_length=12, choices=SESSION_TYPES, default="swim")
    start_dt = models.DateTimeField()
    location_name = models.CharField(max_length=140, blank=True, default="")
    lat = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    lon = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    capacity = models.PositiveIntegerField(default=6)
    status = models.CharField(max_length=12, default="open")  # open/closed
    created_at = models.DateTimeField(auto_now_add=True)

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="BuddyParticipant", related_name="buddy_sessions"
    )

    class Meta:
        ordering = ["start_dt"]

    def __str__(self):
        return f"{self.title} @ {self.start_dt:%Y-%m-%d %H:%M}"

    @property
    def count(self) -> int:
        return self.participants.count()

    @property
    def spots_left(self) -> int:
        return max(self.capacity - self.count, 0)

    def is_joined(self, user) -> bool:
        if not user or not user.is_authenticated:
            return False
        return self.participants.filter(pk=user.pk).exists()


class BuddyParticipant(models.Model):
    session = models.ForeignKey(BuddySession, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("session", "user")]


class BuddyMessage(models.Model):
    session = models.ForeignKey(BuddySession, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user}: {self.body[:30]}"
