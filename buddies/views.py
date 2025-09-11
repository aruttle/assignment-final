# buddies/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import BuddySession, BuddyParticipant, BuddyMessage, SESSION_TYPES
from .forms import BuddySessionForm


def session_list(request):
    qs = BuddySession.objects.filter(start_dt__gte=timezone.now(), status="open")
    t = request.GET.get("type") or ""
    q = request.GET.get("q") or ""

    if t in {"swim", "kayak", "hike", "cycle"}:
        qs = qs.filter(type=t)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(location_name__icontains=q))

    ctx = {
        "sessions": qs,
        "selected_type": t,
        "q": q,
        "type_choices": SESSION_TYPES,  # used by the template <select>
    }

    if getattr(request, "htmx", False):
        return render(request, "buddies/partials/_list.html", ctx)
    return render(request, "buddies/list.html", ctx)


@login_required
def session_create(request):
    if request.method == "POST":
        form = BuddySessionForm(request.POST)
        if form.is_valid():
            sess = form.save(commit=False)
            sess.creator = request.user
            sess.save()
            # creator auto-joins
            BuddyParticipant.objects.get_or_create(session=sess, user=request.user)
            return redirect("buddies:detail", pk=sess.pk)
    else:
        form = BuddySessionForm()
    return render(request, "buddies/create.html", {"form": form})


def session_detail(request, pk):
    sess = get_object_or_404(BuddySession, pk=pk)
    messages = sess.messages.select_related("user")
    joined = sess.is_joined(request.user)
    return render(
        request,
        "buddies/detail.html",
        {"sess": sess, "messages": messages, "joined": joined},
    )


@require_POST
@login_required
def toggle_join(request, pk):
    sess = get_object_or_404(BuddySession, pk=pk)
    joined = sess.is_joined(request.user)

    if joined:
        BuddyParticipant.objects.filter(session=sess, user=request.user).delete()
    else:
        if sess.spots_left <= 0:
            return render(
                request,
                "buddies/partials/_join_box.html",
                {"sess": sess, "joined": joined, "error": "Session is full."},
            )
        BuddyParticipant.objects.get_or_create(session=sess, user=request.user)

    sess.refresh_from_db()
    joined = sess.is_joined(request.user)  # recompute after change
    return render(request, "buddies/partials/_join_box.html", {"sess": sess, "joined": joined})


@require_POST
@login_required
def post_message(request, pk):
    sess = get_object_or_404(BuddySession, pk=pk)
    body = (request.POST.get("body") or "").strip()
    if not body:
        return render(
            request,
            "buddies/partials/_message_item.html",
            {"msg": None, "error": "Message required."},
        )
    msg = BuddyMessage.objects.create(session=sess, user=request.user, body=body)
    return render(request, "buddies/partials/_message_item.html", {"msg": msg})
