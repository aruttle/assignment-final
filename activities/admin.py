from django.contrib import admin
from .models import Provider, Activity, Booking

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_email")
    search_fields = ("name",)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "provider", "price", "duration_minutes", "capacity")
    list_filter = ("provider",)
    search_fields = ("title", "description")

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "start_dt", "party_size", "status")
    list_filter = ("status", "activity__provider")
    search_fields = ("activity__title", "user__username", "user__email")
