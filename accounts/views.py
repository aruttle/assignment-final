from __future__ import annotations

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls import reverse
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

from .forms import SignUpForm, BootstrapAuthenticationForm

# Feature models
from activities.models import Booking
from buddies.models import BuddySession, BuddyMessage


def signup(request):
    next_url = request.GET.get("next") or reverse("my_bookings")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(next_url)
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form, "next": next_url})


class NiceLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = BootstrapAuthenticationForm


# -----------------------------
# Dashboard (/me/)
# -----------------------------
def _first_present(model, candidates: list[str]) -> str | None:
    """
    Return the first attribute name that exists on the model, or None.
    Lets us adapt to slightly different field names.
    """
    try:
        names = {f.name for f in model._meta.get_fields()}
        for c in candidates:
            if c in names:
                return c
    except Exception:
        pass
    return None


@login_required
def me_dashboard(request):
    """
    Unified dashboard:
      - Upcoming bookings (top 4)
      - Buddy sessions you host & joined (top 4 each)
      - Recent buddy messages (top 5)
    """
    now = timezone.now()

    # --- Bookings ---
    booking_dt = _first_present(
        Booking, ["start_dt", "start_time", "start_at", "starts_at", "start", "date"]
    )
    bookings_qs = Booking.objects.filter(user=request.user)
    if booking_dt:
        bookings = bookings_qs.filter(**{f"{booking_dt}__gte": now}).order_by(booking_dt)[:4]
    else:
        bookings = bookings_qs.order_by("-id")[:4]

    # --- Buddy sessions (hosting & joined) ---
    owner_field = _first_present(BuddySession, ["host", "creator", "created_by", "owner", "user"])
    session_dt = _first_present(
        BuddySession, ["start_dt", "start_time", "start_at", "start", "date"]
    )

    if owner_field:
        hosting = BuddySession.objects.filter(**{owner_field: request.user})
    else:
        hosting = BuddySession.objects.none()

    # IMPORTANT: participants is an M2M to User → use participants=request.user
    joined = BuddySession.objects.filter(participants=request.user).distinct()
    if owner_field:
        joined = joined.exclude(**{owner_field: request.user})

    if session_dt:
        hosting = hosting.filter(**{f"{session_dt}__gte": now}).order_by(session_dt)[:4]
        joined = joined.filter(**{f"{session_dt}__gte": now}).order_by(session_dt)[:4]
    else:
        hosting = hosting.order_by("-id")[:4]
        joined = joined.order_by("-id")[:4]

    # --- Recent messages in sessions hosted or joined ---
    msg_time = _first_present(BuddyMessage, ["created", "created_at", "timestamp"])
    msgs = BuddyMessage.objects.filter(
        Q(session__participants=request.user)
        | (Q(**{f"session__{owner_field}": request.user}) if owner_field else Q(pk__in=[]))
    ).select_related("user", "session").distinct()

    if msg_time:
        msgs = msgs.order_by(f"-{msg_time}")[:5]
    else:
        msgs = msgs.order_by("-id")[:5]

    ctx = {
        "bookings": bookings,
        "hosting": hosting,
        "joined": joined,
        "messages": msgs,
        "booking_dt_field": booking_dt,
        "session_dt_field": session_dt,
        "msg_time_field": msg_time,
    }
    return render(request, "accounts/me.html", ctx)
