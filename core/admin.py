from django.contrib import admin
from .models import Spot
from activities.models import Activity, Provider  

class ActivityInline(admin.TabularInline):
    model = Activity
    fields = ("title", "provider", "price", "capacity")  
    autocomplete_fields = ("provider",)                  
    extra = 0

@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "lat", "lon", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("name", "notes")
    inlines = [ActivityInline]
