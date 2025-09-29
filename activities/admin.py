from django.contrib import admin
from django.utils.html import format_html

from .models import Provider, Activity, Booking


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_email")
    search_fields = ("name", "contact_email")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "provider",
        "price",
        "capacity",
        "spot",
        "image_preview",  # small thumbnail in list
    )
    list_filter = ("provider", "spot")
    search_fields = ("title", "description", "provider__name", "spot__name")
    list_select_related = ("provider", "spot")

    # Show image upload + read-only preview on the edit page
    readonly_fields = ("created_at", "image_preview")
    fields = (
        "title",
        "provider",
        "spot",
        "price",
        "duration_minutes",
        "capacity",
        "description",
        "image",
        "image_preview",
        "created_at",
    )

    @admin.display(description="Cover")
    def image_preview(self, obj):
        """Small thumbnail in changelist/detail; fall back to dash."""
        if getattr(obj, "image", None):
            try:
                return format_html(
                    '<img src="{}" style="height:60px;border-radius:6px;object-fit:cover;" />',
                    obj.image.url,
                )
            except Exception:
                pass
        return "–"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "start_dt", "party_size", "status")
    list_filter = ("status", "activity__provider")
    search_fields = ("activity__title", "user__username", "user__email")
    date_hierarchy = "start_dt"
    list_select_related = ("activity", "activity__provider", "user")
