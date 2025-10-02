from django.contrib import admin
from django.utils.html import format_html

from .models import Provider, Activity, Booking, ActivityRSVP


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_email")
    search_fields = ("name", "contact_email")


class RSVPsInline(admin.TabularInline):
    model = ActivityRSVP
    extra = 0
    readonly_fields = ("user", "created_at")
    can_delete = True


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "provider",
        "price",
        "requires_booking",
        "capacity",
        "spot",
        "image_preview",
    )
    list_filter = ("provider", "requires_booking", "spot")
    search_fields = ("title", "description", "provider__name", "spot__name")
    list_select_related = ("provider", "spot")
    list_per_page = 25
    save_on_top = True
    ordering = ("title",)
    inlines = [RSVPsInline]

    readonly_fields = ("created_at", "image_preview")
    fields = (
        "title",
        "provider",
        "spot",
        "description",
        "image",
        "image_preview",
        "price",
        "requires_booking",
        "duration_minutes",
        "capacity",
        "created_at",
    )

    @admin.display(description="Cover")
    def image_preview(self, obj):
        if getattr(obj, "image", None):
            try:
                return format_html(
                    '<img src="{}" style="height:60px;border-radius:6px;object-fit:cover;" alt="Cover preview" />',
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


@admin.register(ActivityRSVP)
class ActivityRSVPAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "created_at")
    search_fields = ("activity__title", "user__username", "user__email")
    list_select_related = ("activity", "user")
    date_hierarchy = "created_at"
