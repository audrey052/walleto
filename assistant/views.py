"""The Assistant page (assistant spec, add-assistant design decision 5).

Sign-in is enforced by LoginRequiredMiddleware. Every lookup goes through the
signed-in user's conversations, so another user's IDs give 404.
"""

from datetime import datetime, time

from django.conf import settings
from django.db import transaction
from django.db.models import Max, OuterRef, Subquery
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.htmx import is_htmx
from core.sections import SECTIONS_BY_KEY
from finance.forms import TransactionForm
from finance.models import Transaction

from . import agent, llm
from .models import Conversation, Message

SUGGESTIONS = [
    "How much did I spend this month?",
    "Am I within my budget?",
    "How are my savings goals going?",
]
ERROR_TEXT = "The assistant couldn't answer right now. Try again."


HISTORY_LIMIT = 30


def _conversation(user, chat_id=None):
    """The chosen conversation (404 for anyone else's), else the latest, created on first use."""
    own = Conversation.objects.for_user(user)
    if chat_id:
        try:
            return get_object_or_404(own, pk=int(chat_id))
        except (TypeError, ValueError):
            raise Http404
    return own.first() or Conversation.objects.create(user=user)


def _history(user):
    """Conversations with at least one question, most recent activity first, titled by their first question."""
    first_question = Message.objects.filter(conversation=OuterRef("pk"), role=Message.Role.USER).order_by("created_at", "id")
    return list(
        Conversation.objects.for_user(user)
        .annotate(title=Subquery(first_question.values("text")[:1]), last_at=Max("messages__created_at"))
        .filter(title__isnull=False)
        .order_by("-last_at", "-id")[:HISTORY_LIMIT]
    )


def _asked_today(user):
    start = timezone.make_aware(datetime.combine(timezone.localdate(), time.min))
    return Message.objects.for_user(user).filter(role=Message.Role.USER, counted=True, created_at__gte=start).count()


def _limit_reached(user):
    return _asked_today(user) >= settings.ASSISTANT_DAILY_LIMIT


def _turns(conversation, *, since_id=None):
    """Questions with their answers, and the cards of the tools used in between."""
    rows = conversation.messages.all()
    if since_id is not None:
        rows = rows.filter(id__gte=since_id)
    turns = []
    for row in rows:
        if row.role == Message.Role.USER:
            turns.append({"question": row, "answer": None, "cards": [], "error": None})
        elif not turns:
            continue
        elif row.role == Message.Role.TOOL:
            turns[-1]["cards"] += [{"card": card, "message_id": row.id} for card in row.cards]
        elif not row.tool_calls:
            turns[-1]["answer"] = row
    return turns


def _page_context(request, conversation):
    return {
        "active_section": SECTIONS_BY_KEY["assistant"],
        "conversation": conversation,
        "turns": _turns(conversation),
        "history": _history(request.user),
        "suggestions": SUGGESTIONS,
        "configured": llm.is_configured(),
        "limit_reached": _limit_reached(request.user),
        "daily_limit": settings.ASSISTANT_DAILY_LIMIT,
    }


def assistant(request):
    conversation = _conversation(request.user, request.GET.get("chat"))
    return render(request, "assistant/assistant.html", _page_context(request, conversation))


@require_POST
def ask(request):
    text = (request.POST.get("question") or "").strip()[:1000]
    conversation = _conversation(request.user, request.POST.get("chat"))
    back = f"{reverse('core:assistant')}?chat={conversation.pk}"
    if not text or not llm.is_configured():
        return redirect(back)
    if _limit_reached(request.user):
        if is_htmx(request):
            return render(request, "assistant/_limit.html", {"daily_limit": settings.ASSISTANT_DAILY_LIMIT})
        return redirect(back)

    error = None
    try:
        answer = agent.ask(conversation, text, user=request.user, today=timezone.localdate(), client=llm.get_client())
        question_id = conversation.messages.filter(role=Message.Role.USER, id__lt=answer.id).last().id
    except llm.AssistantUnavailable:
        error = ERROR_TEXT
        question_id = conversation.messages.filter(role=Message.Role.USER).last().id

    if not is_htmx(request):
        return redirect(back)
    turns = _turns(conversation, since_id=question_id)
    if error:
        turns[-1]["error"] = error
    return render(request, "assistant/_turns.html", {
        "turns": turns,
        "limit_reached": _limit_reached(request.user),
        "daily_limit": settings.ASSISTANT_DAILY_LIMIT,
        "swap_input": True,
    })


@require_POST
def new_chat(request):
    current = Conversation.objects.for_user(request.user).first()
    if current is None or current.messages.exists():
        Conversation.objects.create(user=request.user)
    return redirect("core:assistant")


def _draft(request, message_id):
    """The signed-in user's draft card, locked for update; 404 for anyone else's."""
    row = get_object_or_404(
        Message.objects.for_user(request.user).select_for_update(),
        pk=message_id, role=Message.Role.TOOL, tool_name="add_transaction",
    )
    if not row.cards or row.cards[0].get("type") != "draft":
        raise Http404
    return row


def _card_response(request, row):
    if is_htmx(request):
        return render(request, "assistant/_card_draft.html", {"item": {"card": row.cards[0], "message_id": row.id}})
    return redirect("core:assistant")


@require_POST
def save_draft(request, message_id):
    with transaction.atomic():
        row = _draft(request, message_id)
        card = row.cards[0]
        if card["state"] == "pending":
            fields = card["fields"]
            form = TransactionForm(
                data={
                    "description": fields["description"], "amount": str(fields["amount"]),
                    "category": fields["category_id"], "wallet": fields["wallet_id"],
                    "date": fields["date"], "note": fields.get("note", ""),
                },
                user=request.user,
            )
            if form.is_valid():
                saved = form.save(commit=False)
                saved.source = Transaction.Source.AI
                saved.save()
                card.update(state="saved", transaction_id=saved.pk)
            else:
                card.update(state="invalid", errors=[" ".join(e) for e in form.errors.values()])
            row.save(update_fields=["cards"])
    return _card_response(request, row)


@require_POST
def cancel_draft(request, message_id):
    with transaction.atomic():
        row = _draft(request, message_id)
        if row.cards[0]["state"] == "pending":
            row.cards[0]["state"] = "cancelled"
            row.save(update_fields=["cards"])
    return _card_response(request, row)
