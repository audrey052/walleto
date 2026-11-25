"""One question, answered with tools (add-assistant design decision 3).

The model chooses tools; the tools compute. Every call and result is stored, so
the page can show the cards and later turns can replay the history.
"""

from __future__ import annotations

import json

from django.conf import settings

from . import tools
from .llm import AssistantUnavailable
from .models import Message

HISTORY_MESSAGES = 20

SYSTEM_PROMPT = """You are Walleto's assistant inside a personal finance app for one user in Indonesia.
Today is {today} ({weekday}). Money is Indonesian Rupiah without decimals, written like Rp1.405.500.

Rules:
- Answer only from the results of your tools. Every amount you mention must appear in a tool result; copy its "text" form.
- Never calculate, add up, estimate or convert amounts yourself. If a figure is not in a tool result, call a tool or say you don't have it.
- When a tool returns no data or a note like "No transactions", say so plainly and state no amount.
- If a tool returns an error, fix the arguments and try again, or ask the user.
- To record income or an expense, call add_transaction. It does NOT save: tell the user to check the card and press Save.
- Decline to recommend specific investments, stocks, crypto or other securities, and say you only answer from the data they have recorded. Do not call a tool for that.
- Questions about periods: "this month" is the current month. "The last 7 days", "this past week" or "this week" mean today and the 6 days before; "the last 30 days" means today and the 29 days before. Use 'from'/'to' (YYYY-MM-DD) for them.
- How much is left, or how much can be spent per day, is check_budget. Only when the user asks for a plan or to rearrange their limits, call plan_rest_of_month, then propose_budget_plan with one amount per limited category that add up exactly to what is left. Keep each category realistic against its daily spending so far. The plan is not applied until the user presses Apply to Budget. Without a plan, point the user to the Budget page.
- For a monthly report, call generate_report; the user downloads the PDF from the card.
- Reply in the language of the user's latest message (English or Indonesian), briefly: one to three sentences of plain text, no Markdown. The page shows the figures in a card next to your answer.
"""


def _system(today):
    return SYSTEM_PROMPT.format(today=today.isoformat(), weekday=today.strftime("%A"))


def _history(conversation, before_id):
    """The last stored messages as Chat Completions messages, starting at a question."""
    rows = list(conversation.messages.filter(id__lt=before_id).order_by("-created_at", "-id")[:HISTORY_MESSAGES])
    rows.reverse()
    while rows and rows[0].role != Message.Role.USER:
        rows.pop(0)  # never start with a tool result whose call was cut off
    out = []
    for row in rows:
        if row.role == Message.Role.USER:
            out.append({"role": "user", "content": row.text})
        elif row.role == Message.Role.TOOL:
            out.append({"role": "tool", "tool_call_id": row.tool_call_id, "content": json.dumps(row.tool_result)})
        elif row.tool_calls:
            out.append({"role": "assistant", "content": row.text or None, "tool_calls": row.tool_calls})
        elif row.text:
            out.append({"role": "assistant", "content": row.text})
    return out


def _call_payload(calls):
    return [
        {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": c.raw or json.dumps(c.args)}}
        for c in calls
    ]


def ask(conversation, text, *, user, today, client):
    """Store the question, run up to N tool rounds, store and return the answer row.

    On AssistantUnavailable, everything from this turn except the question is
    removed, the question stops counting toward the daily limit, and the error
    is raised again for the view to show.
    """
    question = Message.objects.create(conversation=conversation, role=Message.Role.USER, text=text, counted=True)
    messages = [{"role": "system", "content": _system(today)}] + _history(conversation, question.id)
    messages.append({"role": "user", "content": text})
    specs = tools.tool_specs(user)
    counted = 0
    try:
        reply = None
        for _round in range(settings.ASSISTANT_MAX_TOOL_ROUNDS):
            reply = client.chat(messages, tools=specs)
            if not reply.tool_calls:
                break
            payload = _call_payload(reply.tool_calls)
            Message.objects.create(conversation=conversation, role=Message.Role.ASSISTANT, text=reply.text, tool_calls=payload)
            messages.append({"role": "assistant", "content": reply.text or None, "tool_calls": payload})
            for call in reply.tool_calls:
                result = tools.run_tool(call.name, call.args, user=user, today=today, client=client)
                counted += result.counted
                Message.objects.create(
                    conversation=conversation, role=Message.Role.TOOL, tool_call_id=call.id,
                    tool_name=call.name, tool_args=call.args, tool_result=result.data, cards=result.cards,
                )
                messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result.data)})
        else:
            # Out of rounds: one last call without tools, so there is always an answer.
            reply = client.chat(messages, tools=None)
    except AssistantUnavailable:
        conversation.messages.filter(id__gt=question.id).delete()
        question.counted = False
        question.save(update_fields=["counted"])
        raise

    return Message.objects.create(
        conversation=conversation, role=Message.Role.ASSISTANT,
        text=reply.text.strip() or "I couldn't find an answer to that.",
        counted_transactions=counted,
    )
