from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, HttpResponse  
from django.contrib import messages 
from .models import BuddySession, BuddyParticipant, BuddyMessage, SESSION_TYPES
from .forms import BuddySessionForm


@login_required
def session_list(request):
    qs = BuddySession.objects.filter(
        start_dt__gte=timezone.now(), status="open"
    ).order_by("start_dt")

    t = request.GET.get("type") or ""
    q = request.GET.get("q") or ""

    allowed_types = {code for code, _ in SESSION_TYPES}
    if t in allowed_types:
        qs = qs.filter(type=t)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(location_name__icontains=q))

    ctx = {
        "sessions": qs,
        "selected_type": t,
        "q": q,
        "type_choices": SESSION_TYPES,
    }

    if getattr(request, "htmx", False):
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
        or request.user.is_staff or request.user.is_superuser
    )
    if not can_delete:
        return HttpResponseForbidden("Not allowed")

    msg.delete()
    # HTMX: remove the <li> by returning nothing and swapping outerHTML
    return HttpResponse("")