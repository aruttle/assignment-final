from django.contrib import admin
from .models import BuddySession, BuddyParticipant, BuddyMessage

@admin.register(BuddySession)
class BuddySessionAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "start_dt", "location_name", "capacity", "status")
    list_filter = ("type", "status")
    search_fields = ("title", "location_name")

@admin.register(BuddyParticipant)
class BuddyParticipantAdmin(admin.ModelAdmin):
    list_display = ("session", "user", "joined_at")
    search_fields = ("session__title", "user__username", "user__email")

@admin.register(BuddyMessage)
class BuddyMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "user", "created_at")
    search_fields = ("session__title", "user__username", "body")
