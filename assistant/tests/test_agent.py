"""assistant spec: the client wrapper and the tool loop, with a fake model."""

from datetime import date
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings

from assistant import agent, llm
from assistant.llm import AssistantUnavailable, FakeClient, Reply, ToolCall
from assistant.models import Conversation, Message
from finance.tests.test_summary import SummaryFixtures

TODAY = date(2026, 11, 15)


def call(name, n=1, **args):
    return ToolCall(id=f"call_{n}", name=name, args=args)


class ClientTests(SimpleTestCase):
    @override_settings(OPENAI_API_KEY="", OPENAI_MODEL="some-model")
    def test_missing_key_is_not_configured(self):
        self.assertFalse(llm.is_configured())

    @override_settings(OPENAI_API_KEY="sk-test", OPENAI_MODEL="")
    def test_missing_model_is_not_configured(self):
        self.assertFalse(llm.is_configured())

    @override_settings(OPENAI_API_KEY="sk-test", OPENAI_MODEL="some-model")
    def test_sdk_errors_become_unavailable(self):
        import openai

        client = llm.OpenAIChat()
        with mock.patch.object(client._client.chat.completions, "create", side_effect=openai.APITimeoutError(request=mock.Mock())):
            with self.assertRaises(AssistantUnavailable):
                client.chat([{"role": "user", "content": "hi"}])

    @override_settings(OPENAI_API_KEY="sk-test", OPENAI_MODEL="some-model", OPENAI_REASONING_EFFORT="")
    def test_reply_with_tool_calls(self):
        client = llm.OpenAIChat()
        message = SimpleNamespace(content=None, tool_calls=[SimpleNamespace(
            id="c1", function=SimpleNamespace(name="check_budget", arguments='{"month": "2026-11"}'))])
        response = SimpleNamespace(choices=[SimpleNamespace(message=message)])
        with mock.patch.object(client._client.chat.completions, "create", return_value=response) as create:
            reply = client.chat([{"role": "user", "content": "budget?"}], tools=[{"type": "function"}])
        self.assertEqual(reply.tool_calls[0].args, {"month": "2026-11"})
        self.assertEqual(create.call_args.kwargs["model"], "some-model")
        self.assertNotIn("reasoning_effort", create.call_args.kwargs)

    @override_settings(OPENAI_API_KEY="sk-test", OPENAI_MODEL="some-model", OPENAI_REASONING_EFFORT="none")
    def test_reasoning_effort_is_sent_when_set(self):
        client = llm.OpenAIChat()
        message = SimpleNamespace(content="Hi", tool_calls=None)
        response = SimpleNamespace(choices=[SimpleNamespace(message=message)])
        with mock.patch.object(client._client.chat.completions, "create", return_value=response) as create:
            self.assertEqual(client.chat([{"role": "user", "content": "hi"}]).text, "Hi")
        self.assertEqual(create.call_args.kwargs["reasoning_effort"], "none")


@override_settings(ASSISTANT_MAX_TOOL_ROUNDS=4)
class AgentTests(SummaryFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.chat = Conversation.objects.create(user=self.user)

    def ask(self, script, text="How much did I spend on food?"):
        client = FakeClient(script)
        answer = agent.ask(self.chat, text, user=self.user, today=TODAY, client=client)
        return answer, client

    def test_one_tool_then_an_answer(self):
        self.add(1_405_500)
        answer, client = self.ask([
            Reply(tool_calls=[call("query_transactions", category="Food & drinks")]),
            Reply(text="You spent Rp1.405.500 on food this month."),
        ])
        self.assertEqual(answer.text, "You spent Rp1.405.500 on food this month.")
        self.assertEqual(answer.counted_transactions, 1)
        tool_row = self.chat.messages.get(role=Message.Role.TOOL)
        self.assertEqual(tool_row.cards[0]["rows"][0], ["Expenses", "Rp1.405.500"])
        # The second call carried the tool result back to the model.
        self.assertEqual(client.calls[1]["messages"][-1]["role"], "tool")
        self.assertIn("1405500", client.calls[1]["messages"][-1]["content"])

    def test_two_tools_in_one_turn(self):
        self.add(100_000)
        answer, _ = self.ask([
            Reply(tool_calls=[call("query_transactions", 1), call("check_budget", 2)]),
            Reply(text="Done."),
        ])
        self.assertEqual(self.chat.messages.filter(role=Message.Role.TOOL).count(), 2)
        self.assertEqual(answer.counted_transactions, 1)

    def test_rounds_are_capped(self):
        script = [Reply(tool_calls=[call("check_budget", n)]) for n in range(1, 6)]
        script.insert(4, Reply(text="Final answer."))  # the 5th call is the one without tools
        answer, client = self.ask(script)
        self.assertEqual(len(client.calls), 5)
        self.assertIsNone(client.calls[-1]["tools"])
        self.assertEqual(answer.text, "Final answer.")

    def test_stock_tip_calls_no_tool(self):
        answer, client = self.ask([Reply(text="I can't recommend stocks.")], text="Which stock should I buy?")
        self.assertEqual(len(client.calls), 1)
        self.assertIn("Decline to recommend specific investments", client.calls[0]["messages"][0]["content"])
        self.assertFalse(self.chat.messages.filter(role=Message.Role.TOOL).exists())
        self.assertEqual(answer.text, "I can't recommend stocks.")

    def test_history_is_replayed(self):
        self.ask([Reply(tool_calls=[call("check_budget")]), Reply(text="First answer.")], text="Budget?")
        _, client = self.ask([Reply(text="Second answer.")], text="And now?")
        roles = [m["role"] for m in client.calls[0]["messages"]]
        self.assertEqual(roles, ["system", "user", "assistant", "tool", "assistant", "user"])

    def test_failure_removes_the_turn_and_does_not_count(self):
        with self.assertRaises(AssistantUnavailable):
            self.ask([Reply(tool_calls=[call("check_budget")]), AssistantUnavailable("timeout")])
        question = self.chat.messages.get()
        self.assertEqual(question.role, Message.Role.USER)
        self.assertFalse(question.counted)
