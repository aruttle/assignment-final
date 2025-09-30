from __future__ import annotations

from datetime import datetime, date as date_cls, time as dtime
from dateutil import parser as dtparser

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from .models import Activity, Provider, Booking


# ---------------------------
# Activities: list + detail
# ---------------------------
def activity_list(request):
    # Include provider (and spot if present) for efficient templates
    qs = Activity.objects.select_related("provider", "spot").order_by("title")
    providers = Provider.objects.order_by("name")

    provider_id = request.GET.get("provider") or ""
    q = request.GET.get("q") or ""
    page_num = request.GET.get("page") or "1"

    if provider_id.isdigit():
        qs = qs.filter(provider_id=provider_id)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    paginator = Paginator(qs, 9)  # 9 activity cards per chunk
    page_obj = paginator.get_page(page_num)

    ctx = {
        "activities": page_obj.object_list,
        "object_list": page_obj.object_list,  # some templates refer to object_list
        "page_obj": page_obj,
        "paginator": paginator,
        "providers": providers,
        "selected_provider": provider_id,
        "q": q,
    }

    # HTMX requests receive just the next chunk
    if request.headers.get("HX-Request"):
        return render(request, "activities/partials/_list.html", ctx)

    return render(request, "activities/list.html", ctx)


def activity_detail(request, pk: int):
    activity = get_object_or_404(
        Activity.objects.select_related("provider", "spot"),
        pk=pk
    )
    today = timezone.localdate()
    return render(request, "activities/detail.html", {"activity": activity, "today": today})


# ---------------------------
# Availability helpers
# ---------------------------
def _slot_hours() -> list[int]:
    return [9, 11, 13, 15]


def _make_aware(dt: datetime) -> datetime:
    tz = timezone.get_current_timezone()
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, tz)
    return dt.astimezone(tz)


def _available_slots(activity: Activity, the_date: date_cls, user=None) -> list[dict]:
    """
    Returns list of dicts:
      [{'dt': aware_dt, 'iso': str, 'label': 'HH:MM', 'remaining': int, 'mine': bool}]
    If `user` provided, 'mine' marks a slot the user already booked (confirmed).
    """
    slots: list[dict] = []
    user_id = getattr(user, "id", None)

    # Preload my confirmed bookings for that day to mark 'mine'
    my_slot_set = set()
    if user_id:
        day_start = _make_aware(datetime.combine(the_date, dtime(0, 0)))
        day_end = _make_aware(datetime.combine(the_date, dtime(23, 59)))
        my_slot_set = set(
            Booking.objects.filter(
                user_id=user_id,
                activity=activity,
                status="confirmed",
                start_dt__gte=day_start,
                start_dt__lte=day_end,
            ).values_list("start_dt", flat=True)
        )

    for hour in _slot_hours():
        naive = datetime.combine(the_date, dtime(hour=hour, minute=0))
        start_dt = _make_aware(naive)

        taken = (
            Booking.objects.filter(activity=activity, start_dt=start_dt, status="confirmed")
            .aggregate(total=Sum("party_size"))["total"]
            or 0
        )
        remaining = max(activity.capacity - taken, 0)
        if remaining > 0:
            slots.append(
                {
                    "dt": start_dt,
                    "iso": start_dt.isoformat(),
                    "label": start_dt.strftime("%H:%M"),
                    "remaining": remaining,
                    "mine": (start_dt in my_slot_set),
                }
            )
    return slots


# ---------------------------
# HTMX: availability + book
# ---------------------------
def activity_availability(request, pk: int):
    activity = get_object_or_404(Activity.objects.select_related("provider"), pk=pk)
    date_str = request.GET.get("date", "")
    try:
        the_date = dtparser.parse(date_str).date()
    except Exception:
        the_date = timezone.localdate()

    slots = _available_slots(activity, the_date, user=request.user if request.user.is_authenticated else None)
    ctx = {"activity": activity, "date": the_date, "slots": slots}
    return render(request, "activities/partials/_slots.html", ctx)


@login_required
def booking_create(request, pk: int):
    activity = get_object_or_404(Activity, pk=pk)

    start_iso = request.POST.get("start_dt", "")
    party_size_raw = request.POST.get("party_size", "1")

    # Parse start
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

    # party_size
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

    # Duplicate (same slot by same user) guard
    if Booking.objects.filter(
        user=request.user, activity=activity, start_dt=start_dt, status="confirmed"
    ).exists():
        return render(
            request,
            "activities/partials/_booking_panel.html",
            {"activity": activity, "error": "You already have this time booked."},
        )

    # Capacity check
    valid_slots = _available_slots(activity, start_dt.date(), user=request.user)
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


# ---------------------------
# My bookings + cancel (delete)
# ---------------------------
@login_required
def my_bookings(request):
    bookings = (
        Booking.objects.filter(user=request.user)
        .select_related("activity", "activity__provider")
        .order_by("-created_at")
    )
    return render(request, "activities/my_bookings.html", {"bookings": bookings})


@login_required
def booking_cancel(request, pk: int):
    booking = get_object_or_404(
        Booking.objects.select_related("activity", "activity__provider"),
        pk=pk,
    )
    if booking.user_id != request.user.id and not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Not allowed")

    if request.method == "POST":
        booking.delete()
        if request.headers.get("HX-Request"):
            return HttpResponse("")  # removes the row
        return redirect("my_bookings")

    return redirect("my_bookings")
