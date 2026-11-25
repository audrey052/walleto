"""Score the Assistant's tool choice against evals/assistant.jsonl (add-assistant design decision 7).

Calls the real model with the demo user's data, once per question, and appends
a table to docs/eval_results.md. Never run by the test suite.
"""

import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from assistant import agent, llm, tools
from assistant.evaluation import markdown, score
from finance.demo import DEMO_EMAIL

CASES = Path(settings.BASE_DIR) / "evals" / "assistant.jsonl"
RESULTS = Path(settings.BASE_DIR) / "docs" / "eval_results.md"


class Command(BaseCommand):
    help = "Score the assistant's tool choice, arguments and refusals with the real model."

    def add_arguments(self, parser):
        parser.add_argument("--label", default="Run", help="Heading for this run in docs/eval_results.md")
        parser.add_argument("--no-write", action="store_true", help="Print only")

    def handle(self, *args, label, no_write, **options):
        if not llm.is_configured():
            raise CommandError("Set OPENAI_API_KEY and OPENAI_MODEL in .env first.")
        user = get_user_model().objects.filter(email=DEMO_EMAIL).first()
        if user is None:
            raise CommandError("No demo user. Run `python manage.py seed_demo` first.")
        today = timezone.localdate()
        client = llm.get_client()
        specs = tools.tool_specs(user)
        cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]

        scores = []
        for case in cases:
            messages = [{"role": "system", "content": agent._system(today)}, {"role": "user", "content": case["question"]}]
            try:
                reply = client.chat(messages, tools=specs)
            except llm.AssistantUnavailable as exc:
                raise CommandError(f"Model call failed on {case['id']}: {exc}") from exc
            result = score(case, reply, today)
            scores.append(result)
            self.stdout.write(f"{'pass' if result.passed else 'FAIL'}  {case['id']:<16} {result.got}  {result.note}")

        text = markdown(scores, model=settings.OPENAI_MODEL, today=today, label=label)
        self.stdout.write("\n" + text)
        if not no_write:
            header = "# Evaluation results\n\nAssistant tool choice, arguments and refusals (`python manage.py eval_assistant`).\n\n"
            existing = RESULTS.read_text(encoding="utf-8") if RESULTS.exists() else header
            RESULTS.write_text(existing.rstrip("\n") + "\n\n" + text, encoding="utf-8")
            self.stdout.write(f"Written to {RESULTS}")
