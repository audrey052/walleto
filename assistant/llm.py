"""The only module that talks to OpenAI (add-assistant design decision 4).

`get_client()` returns `OpenAIChat` when the key and model are set. Tests swap
it for `FakeClient`, so no test calls the network or needs a key.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from django.conf import settings

TIMEOUT_SECONDS = 30


class AssistantUnavailable(Exception):
    """The model could not be reached or failed; the page shows a short message."""


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict  # {} when the model sent invalid JSON; `raw` keeps what it sent
    raw: str = ""


@dataclass
class Reply:
    text: str = ""
    tool_calls: list = field(default_factory=list)


def is_configured():
    return bool(settings.OPENAI_API_KEY and settings.OPENAI_MODEL)


def _parse_args(raw):
    try:
        value = json.loads(raw or "{}")
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


class OpenAIChat:
    """Chat Completions with tool calling, one method wide."""

    def __init__(self):
        import openai  # imported here so tests without the key never touch it

        self._openai = openai
        self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY, timeout=TIMEOUT_SECONDS, max_retries=1)

    def chat(self, messages, tools=None, tool_choice="auto"):
        kwargs = {"model": settings.OPENAI_MODEL, "messages": messages}
        if settings.OPENAI_REASONING_EFFORT:
            kwargs["reasoning_effort"] = settings.OPENAI_REASONING_EFFORT
        if tools:
            kwargs.update(tools=tools, tool_choice=tool_choice)
        try:
            response = self._client.chat.completions.create(**kwargs)
        except self._openai.OpenAIError as exc:
            raise AssistantUnavailable(str(exc)) from exc
        message = response.choices[0].message
        calls = []
        for call in message.tool_calls or []:
            args = _parse_args(call.function.arguments)
            calls.append(ToolCall(call.id, call.function.name, args if args is not None else {}, call.function.arguments or ""))
        return Reply(text=message.content or "", tool_calls=calls)


class FakeClient:
    """Replays scripted replies in order and records what it was sent.

    A script item is a Reply, or an exception instance to raise.
    """

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def chat(self, messages, tools=None, tool_choice="auto"):
        self.calls.append({"messages": messages, "tools": tools, "tool_choice": tool_choice})
        if not self.script:
            return Reply(text="(no scripted reply)")
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def get_client():
    return OpenAIChat()
