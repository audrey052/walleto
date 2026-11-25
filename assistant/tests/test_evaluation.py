"""add-assistant design decision 7: scoring, tested with fake replies."""

import json
from datetime import date
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from assistant.evaluation import markdown, score
from assistant.llm import Reply, ToolCall

TODAY = date(2026, 11, 25)


class ScoringTests(SimpleTestCase):
    def test_right_tool_and_arguments(self):
        case = {"id": "grab", "question": "grab 18k kemarin pakai OVO",
                "expect": {"tool": "add_transaction", "args": {"amount": 18000, "wallet": "OVO", "date": "{yesterday}"},
                           "optional": ["description", "category"]}}
        reply = Reply(tool_calls=[ToolCall("c1", "add_transaction", {
            "amount": "18000", "wallet": "ovo", "date": "2026-11-24", "description": "Grab", "category": "Transport"})])
        self.assertTrue(score(case, reply, TODAY).passed)

    def test_wrong_argument_and_refusal(self):
        case = {"id": "food", "question": "food last month?",
                "expect": {"tool": "query_transactions", "args": {"category": "Food & drinks", "month": "{last_month}"}}}
        wrong = score(case, Reply(tool_calls=[ToolCall("c1", "query_transactions", {"category": "Food & drinks", "month": "2026-11"})]), TODAY)
        self.assertTrue(wrong.tool_ok)
        self.assertFalse(wrong.passed)
        self.assertIn("month: expected '2026-10'", wrong.note)

        refuse = {"id": "stock", "question": "Which stock?", "expect": {"refuse": True}}
        self.assertTrue(score(refuse, Reply(text="I can't help with that."), TODAY).passed)
        self.assertFalse(score(refuse, Reply(tool_calls=[ToolCall("c1", "query_transactions", {})]), TODAY).passed)

    def test_markdown_table(self):
        case = {"id": "stock", "question": "Which stock?", "expect": {"refuse": True}}
        text = markdown([score(case, Reply(text="No."), TODAY)], model="m", today=TODAY, label="Run 1")
        self.assertIn("**Refused correctly:** 1 of 1", text)
        self.assertIn("| stock | Which stock? | `refuse` | `no tool` | pass |", text)

    def test_cases_file(self):
        lines = (Path(settings.BASE_DIR) / "evals" / "assistant.jsonl").read_text(encoding="utf-8").splitlines()
        cases = [json.loads(line) for line in lines if line.strip()]
        self.assertGreaterEqual(len(cases), 20)
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        self.assertGreaterEqual(sum(1 for c in cases if c["expect"].get("refuse")), 4)
