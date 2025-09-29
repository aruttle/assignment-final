from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, Count
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BuddySessionForm
from .models import BuddySession, BuddyParticipant, BuddyMessage, SESSION_TYPES

PAGE_SIZE_SESSIONS = 6  


@login_required
def session_list(request):
    """
    Buddies landing page: show only upcoming & open sessions.
    Optional filters:
      - ?type=<code> via chips
      - ?q=<free text>  (matches title/location)
    """
    qs = (
        BuddySession.objects
        .filter(start_dt__gte=timezone.now(), status="open")
        .annotate(joined_count=Count("participants", distinct=True))
        .order_by("start_dt")
    )

    t = (request.GET.get("type") or "").strip()
    q = (request.GET.get("q") or "").strip()

    allowed_types = {code for code, _ in SESSION_TYPES}
    if t in allowed_types:
        qs = qs.filter(type=t)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(location_name__icontains=q))

    # Pagination
    page = request.GET.get("page", "1")
    paginator = Paginator(qs, PAGE_SIZE_SESSIONS)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    ctx = {
        "sessions": page_obj.object_list,
        "page_obj": page_obj,
        "open_count": paginator.count,
        "selected_type": t,
        "q": q,
        "type_choices": SESSION_TYPES,
    }

    # HTMX fragment 
    if request.headers.get("HX-Request"):
        return render(request, "buddies/partials/_list.html", ctx)

    return render(request, "buddies/list.html", ctx)


@login_required
def session_create(request):
    if request.method == "POST":
        form = BuddySessionForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.creator = request.user
            obj.save()
            messages.success(request, "Buddy session created.")
            return redirect("buddies:detail", obj.id)
    else:
        form = BuddySessionForm()
    return render(request, "buddies/create.html", {"form": form})


@login_required
def session_detail(request, pk):
    sess = get_object_or_404(BuddySession, pk=pk)
    msgs = sess.messages.select_related("user").order_by("-created_at")
    joined = sess.is_joined(request.user)
    return render(
        request,
        "buddies/detail.html",
        {"sess": sess, "messages": msgs, "joined": joined},
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
    joined = sess.is_joined(request.user)
    return render(
        request,
        "buddies/partials/_join_box.html",
        {"sess": sess, "joined": joined},
    )


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


@login_required
def session_edit(request, pk):
    sess = get_object_or_404(BuddySession, pk=pk)
    is_owner = (sess.creator_id == request.user.id)
    if not (is_owner or request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Not allowed")

    if request.method == "POST":
        form = BuddySessionForm(request.POST, instance=sess)
        if form.is_valid():
            form.save()
            messages.success(request, "Buddy session updated.")
            return redirect("buddies:detail", sess.id)
    else:
        form = BuddySessionForm(instance=sess)

    return render(request, "buddies/edit.html", {"form": form, "sess": sess})


@login_required
def session_delete(request, pk):
    sess = get_object_or_404(BuddySession, pk=pk)
    is_owner = (sess.creator_id == request.user.id)
    if not (is_owner or request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Not allowed")
    if request.method == "POST":
        title = sess.title
        sess.delete()
        messages.success(request, f"Deleted session: {title}")
        return redirect("buddies:list")
    return redirect("buddies:detail", pk=sess.id)


@require_POST
@login_required
def delete_message(request, msg_id):
    msg = get_object_or_404(BuddyMessage.objects.select_related("session"), pk=msg_id)
    can_delete = (
        msg.user_id == request.user.id
        or request.user.id == getattr(msg.session, "creator_id", None)
        or request.user.is_staff
        or request.user.is_superuser
    )
    if not can_delete:
        return HttpResponseForbidden("Not allowed")

    msg.delete()
    return HttpResponse("")


@login_required
def my_sessions(request):
    """
    Upcoming sessions the user hosts OR has joined.
    """
    now = timezone.now()
    sessions = (
        BuddySession.objects
        .filter(Q(creator=request.user) | Q(participants=request.user), start_dt__gte=now)
        .select_related("creator")
        .annotate(joined_count=Count("participants", distinct=True))
        .order_by("start_dt")
        .distinct()
    )
    return render(request, "buddies/my_sessions.html", {"sessions": sessions})
