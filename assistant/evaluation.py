"""Scoring for `manage.py eval_assistant` (add-assistant design decision 7).

Only the model's first reply to each question is scored: which tool it chose,
with which arguments, or whether it declined. Kept apart from the command so it
can be tested with fake replies.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta

from finance.months import month_param, shift


def placeholders(today):
    last = shift(today.year, today.month, -1)
    return {
        "{today}": today.isoformat(),
        "{yesterday}": (today - timedelta(days=1)).isoformat(),
        "{days_ago_6}": (today - timedelta(days=6)).isoformat(),
        "{this_month}": month_param(today.year, today.month),
        "{last_month}": month_param(*last),
    }


def _fill(value, names):
    if isinstance(value, str):
        return names.get(value, value)
    return value


def _same(expected, actual):
    if isinstance(expected, int) and not isinstance(expected, bool):
        try:
            return int(actual) == expected
        except (TypeError, ValueError):
            return False
    return str(expected).strip().casefold() == str(actual).strip().casefold()


@dataclass
class Score:
    case_id: str
    question: str
    expected: str
    got: str
    tool_ok: bool
    args_ok: bool
    note: str = ""

    @property
    def passed(self):
        return self.tool_ok and self.args_ok


def score(case, reply, today):
    """Compare one case with the model's first reply."""
    expect = case["expect"]
    first = reply.tool_calls[0] if reply.tool_calls else None
    got = f"{first.name}({json.dumps(first.args, ensure_ascii=False)})" if first else "no tool"
    if expect.get("refuse"):
        ok = first is None
        return Score(case["id"], case["question"], "refuse", got, ok, ok, "" if ok else "called a tool")
    expected = f"{expect['tool']}({json.dumps(expect.get('args', {}), ensure_ascii=False)})"
    if first is None or first.name != expect["tool"]:
        return Score(case["id"], case["question"], expected, got, False, False, "wrong tool")
    names = placeholders(today)
    wanted = {k: _fill(v, names) for k, v in expect.get("args", {}).items()}
    allowed = set(wanted) | set(expect.get("optional", []))
    problems = [f"{k}: expected {v!r}, got {first.args.get(k)!r}" for k, v in wanted.items() if not _same(v, first.args.get(k))]
    extra = sorted(set(first.args) - allowed)
    if extra:
        problems.append("unexpected " + ", ".join(extra))
    return Score(case["id"], case["question"], expected, got, True, not problems, "; ".join(problems))


def markdown(scores, *, model, today, label):
    total = len(scores)
    refusals = [s for s in scores if s.expected == "refuse"]
    lookups = [s for s in scores if s.expected != "refuse"]
    lines = [
        f"## {label}",
        "",
        f"- **Model:** `{model}`",
        f"- **Date:** {today.isoformat()}, demo account",
        f"- **Passed:** {sum(s.passed for s in scores)} of {total}",
        f"- **Tool chosen correctly:** {sum(s.tool_ok for s in lookups)} of {len(lookups)}",
        f"- **Arguments correct:** {sum(s.passed for s in lookups)} of {len(lookups)}",
        f"- **Refused correctly:** {sum(s.passed for s in refusals)} of {len(refusals)}",
        "",
        "| Case | Question | Expected | Got | Result |",
        "|---|---|---|---|---|",
    ]
    for s in scores:
        result = "pass" if s.passed else f"fail: {s.note}"
        lines.append(f"| {s.case_id} | {s.question} | `{s.expected}` | `{s.got}` | {result} |")
    return "\n".join(lines) + "\n"
