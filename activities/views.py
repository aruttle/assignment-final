# activities/views.py
from datetime import datetime, date, time as dtime

from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from dateutil import parser as dtparser

from .models import Activity, Provider, Booking


# ---------------------------
# Activities: list + detail
# ---------------------------
def activity_list(request):
    qs = Activity.objects.select_related("provider")
    providers = Provider.objects.order_by("name")

    provider_id = request.GET.get("provider") or ""
    q = request.GET.get("q") or ""

    if provider_id.isdigit():
        qs = qs.filter(provider_id=provider_id)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    ctx = {"activities": qs, "providers": providers, "selected_provider": provider_id, "q": q}

    if getattr(request, "htmx", False):
        return render(request, "activities/partials/_list.html", ctx)
    return render(request, "activities/list.html", ctx)


def activity_detail(request, pk):
    activity = get_object_or_404(Activity.objects.select_related("provider"), pk=pk)
    return render(request, "activities/detail.html", {"activity": activity})


# ---------------------------
# Availability helpers
# ---------------------------
def _slot_hours():
    # Demo window; adjust later or make per-activity
    return [9, 11, 13, 15]


def _make_aware(dt: datetime):
    tz = timezone.get_current_timezone()
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, tz)
    return dt.astimezone(tz)


def _available_slots(activity: Activity, the_date: date):
    """
    Returns: list of dicts like:
      [{'dt': aware_dt, 'iso': str, 'label': 'HH:MM', 'remaining': int}]
    """
    slots = []
    for hour in _slot_hours():
        naive = datetime.combine(the_date, dtime(hour=hour, minute=0))
        start_dt = _make_aware(naive)
        total = (
            Booking.objects.filter(activity=activity, start_dt=start_dt, status="confirmed")
            .aggregate(total=Sum("party_size"))["total"]
            or 0
        )
        remaining = max(activity.capacity - total, 0)
        if remaining > 0:
            slots.append(
                {
                    "dt": start_dt,
                    "iso": start_dt.isoformat(),
                    "label": start_dt.strftime("%H:%M"),
                    "remaining": remaining,
                }
            )
    return slots


# ---------------------------
# HTMX: availability + book
# ---------------------------
def activity_availability(request, pk: int):
    """Returns slot buttons for a given date (partial)."""
    activity = get_object_or_404(Activity.objects.select_related("provider"), pk=pk)
    date_str = request.GET.get("date", "")
    try:
        the_date = dtparser.parse(date_str).date()
    except Exception:
        the_date = timezone.localdate()

    slots = _available_slots(activity, the_date)
    ctx = {"activity": activity, "date": the_date, "slots": slots}
    return render(request, "activities/partials/_slots.html", ctx)


def booking_create(request, pk: int):
    """Create a booking (HTMX). Returns booking panel partial or inline error."""
    activity = get_object_or_404(Activity, pk=pk)

    # Require login (use admin login for now)
    if not request.user.is_authenticated:
        resp = HttpResponse("")
        resp["HX-Redirect"] = f"/admin/login/?next=/activities/{pk}/"
        return resp

    start_iso = request.POST.get("start_dt", "")
    party_size_raw = request.POST.get("party_size", "1")

    # Parse start_dt
    try:
        parsed = dtparser.isoparse(start_iso) if start_iso else None
        if not parsed:
            raise ValueError("Missing start time")
        start_dt = _make_aware(parsed)
    except Exception:
        return render(
            request,
            "activities/partials/_booking_panel.html",
            {"activity": activity, "error": "Invalid start time."},
        )

    # party_size validation
    try:
        party_size = int(party_size_raw)
        if party_size < 1:
            raise ValueError
    except Exception:
        return render(
            request,
            "activities/partials/_booking_panel.html",
            {"activity": activity, "error": "Party size must be at least 1."},
        )

    # Validate against current availability
    valid_slots = _available_slots(activity, start_dt.date())
    matching = next((s for s in valid_slots if s["dt"] == start_dt), None)
    if not matching:
        return render(
            request,
            "activities/partials/_booking_panel.html",
            {"activity": activity, "error": "That slot is no longer available."},
        )
    if party_size > matching["remaining"]:
        return render(
            request,
            "activities/partials/_booking_panel.html",
            {
                "activity": activity,
                "error": f"Only {matching['remaining']} seats left for {matching['label']}.",
            },
        )

    # Create booking
    booking = Booking.objects.create(
        user=request.user,
        activity=activity,
        start_dt=start_dt,
        party_size=party_size,
        status="confirmed",
    )
    return render(
        request,
        "activities/partials/_booking_panel.html",
        {"activity": activity, "booking": booking},
    )
