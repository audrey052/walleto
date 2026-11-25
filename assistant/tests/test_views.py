"""assistant spec: the page, questions, drafts, limits and privacy (with a fake model)."""

from datetime import date, datetime
from datetime import timezone as dt_timezone
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from assistant.llm import AssistantUnavailable, FakeClient, Reply, ToolCall
from assistant.models import Conversation, Message
from finance.models import Transaction, Wallet
from finance.tests.test_summary import SummaryFixtures
from finance.tests.test_views import make_user

# 15 Nov 2026, 10:00 in Jakarta.
NOW = datetime(2026, 11, 15, 3, 0, tzinfo=dt_timezone.utc)
HTMX = {"HTTP_HX_REQUEST": "true"}
PAGE = reverse("core:assistant")
ASK = reverse("assistant:ask")


@override_settings(OPENAI_API_KEY="sk-test", OPENAI_MODEL="test-model", ASSISTANT_DAILY_LIMIT=30)
class AssistantPageCase(SummaryFixtures, TestCase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch("django.utils.timezone.now", return_value=NOW)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client.force_login(self.user)

    def script(self, *replies):
        client = FakeClient(replies)
        patcher = mock.patch("assistant.views.llm.get_client", return_value=client)
        patcher.start()
        self.addCleanup(patcher.stop)
        return client

    def ask(self, text, htmx=True):
        return self.client.post(ASK, {"question": text}, **(HTMX if htmx else {}))

    def draft_card(self):
        self.script(
            Reply(tool_calls=[ToolCall("c1", "add_transaction", {
                "description": "Bakmi GM", "amount": 45_000, "category": "Food & drinks", "wallet": "GoPay", "date": "2026-11-15"})]),
            Reply(text="Check the card and press Save."),
        )
        self.ask("Lunch at Bakmi GM 45rb from GoPay today")
        return Message.objects.get(tool_name="add_transaction")


class PageTests(AssistantPageCase):
    def test_empty_conversation(self):
        response = self.client.get(PAGE)
        self.assertContains(response, "<h1>Assistant</h1>", html=True)
        self.assertContains(response, "How much did I spend this month?")
        self.assertContains(response, "Am I within my budget?")
        self.assertContains(response, '<textarea name="question" rows="1" required')
        self.assertNotContains(response, "Not professional financial advice")  # removed at the developer's request
        self.assertNotContains(response, "Coming soon")
        self.assertNotContains(response, "New chat")

    def test_suggestion_and_card(self):
        self.add(1_405_500)
        self.script(Reply(tool_calls=[ToolCall("c1", "query_transactions", {})]), Reply(text="You spent Rp1.405.500 this month."))
        response = self.ask("How much did I spend this month?")
        self.assertContains(response, "How much did I spend this month?")
        self.assertContains(response, "You spent Rp1.405.500 this month.")
        self.assertContains(response, "Rp1.405.500</dd>", html=False)
        self.assertContains(response, "Calculated from 1 transaction")
        self.assertContains(response, 'hx-swap-oob="delete"')

    def test_reload_keeps_the_conversation(self):
        self.script(Reply(text="Hello."))
        self.ask("Hi")
        page = self.client.get(PAGE)
        content = page.content.decode()
        self.assertLess(content.index(">Hi<"), content.index("Hello."))
        self.assertContains(page, "New chat")
        self.assertNotContains(page, "Am I within my budget?")

    def test_without_javascript_the_form_redirects_back(self):
        self.script(Reply(text="Hello."))
        response = self.ask("Hi", htmx=False)
        chat = Conversation.objects.get(user=self.user)
        self.assertRedirects(response, f"{PAGE}?chat={chat.pk}")
        self.assertContains(self.client.get(PAGE), "Hello.")

    def test_new_chat(self):
        self.script(Reply(text="Hello."))
        self.ask("Hi")
        self.client.post(reverse("assistant:new"))
        self.assertEqual(Conversation.objects.for_user(self.user).count(), 2)
        self.assertNotContains(self.client.get(PAGE), "Hello.")
        self.client.post(reverse("assistant:new"))  # an empty chat is reused
        self.assertEqual(Conversation.objects.for_user(self.user).count(), 2)


class HistoryTests(AssistantPageCase):
    def test_earlier_conversations_are_listed_and_can_be_reopened(self):
        self.script(Reply(text="Food answer."), Reply(text="Budget answer."), Reply(text="More food."))
        self.ask("How much on food?")
        first = Conversation.objects.get(user=self.user)
        self.client.post(reverse("assistant:new"))
        self.ask("Am I within budget?")
        page = self.client.get(PAGE)
        self.assertContains(page, "History")
        content = page.content.decode()
        # Newest activity first, titled by the first question.
        self.assertLess(content.index(">Am I within budget?</span>"), content.index(">How much on food?</span>"))
        self.assertContains(page, f'href="{PAGE}?chat={first.pk}"')

        old = self.client.get(PAGE, {"chat": first.pk})
        self.assertContains(old, "Food answer.")
        self.assertNotContains(old, "Budget answer.")
        self.assertContains(old, f'name="chat" value="{first.pk}"')
        # Asking from the reopened chat continues it.
        self.client.post(ASK, {"question": "And last week?", "chat": first.pk}, **HTMX)
        self.assertEqual(first.messages.filter(role=Message.Role.USER).count(), 2)

    def test_no_history_button_before_the_first_question(self):
        self.assertNotContains(self.client.get(PAGE), "Your conversations")

    def test_another_users_conversation(self):
        other = make_user(email="other@example.com", name="Other")
        theirs = Conversation.objects.create(user=other)
        Message.objects.create(conversation=theirs, role=Message.Role.USER, text="Secret question")
        self.assertEqual(self.client.get(PAGE, {"chat": theirs.pk}).status_code, 404)
        self.assertEqual(self.client.get(PAGE, {"chat": "abc"}).status_code, 404)
        self.assertEqual(self.client.post(ASK, {"question": "Hi", "chat": theirs.pk}, **HTMX).status_code, 404)
        self.assertNotContains(self.client.get(PAGE), "Secret question")


class LimitAndFailureTests(AssistantPageCase):
    @override_settings(ASSISTANT_DAILY_LIMIT=2)
    def test_daily_limit(self):
        client = self.script(Reply(text="One."), Reply(text="Two."), Reply(text="Three."))
        self.ask("1")
        second = self.ask("2")
        self.assertContains(second, "the daily limit")  # the input is swapped right away
        third = self.ask("3")
        self.assertContains(third, "You've asked 2 questions today, the daily limit.")
        self.assertEqual(len(client.calls), 2)
        self.assertContains(self.client.get(PAGE), "the daily limit")
        self.assertNotContains(self.client.get(PAGE), '<textarea name="question"')

    @override_settings(OPENAI_API_KEY="")
    def test_missing_configuration(self):
        page = self.client.get(PAGE)
        self.assertContains(page, "The assistant isn't set up yet")
        self.assertNotContains(page, 'name="question"')
        response = self.ask("Hi", htmx=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(PAGE))
        self.assertFalse(Message.objects.exists())

    def test_timeout(self):
        self.script(AssistantUnavailable("timed out"))
        response = self.ask("How much did I spend?")
        self.assertContains(response, "The assistant couldn&#x27;t answer right now. Try again.")
        question = Message.objects.get()
        self.assertFalse(question.counted)


class DraftTests(AssistantPageCase):
    def test_confirm_and_save(self):
        row = self.draft_card()
        self.assertEqual(Transaction.objects.count(), 0)  # nothing saved before confirming
        page = self.client.get(PAGE)
        self.assertContains(page, "Check before saving")
        self.assertContains(page, "−Rp45.000")
        response = self.client.post(reverse("assistant:save_draft", args=[row.pk]), **HTMX)
        self.assertContains(response, "Saved to Transactions")
        saved = Transaction.objects.get()
        self.assertEqual((saved.description, saved.amount, saved.category, saved.wallet, saved.date, saved.source),
                         ("Bakmi GM", 45_000, self.food, self.gopay, date(2026, 11, 15), Transaction.Source.AI))
        listing = self.client.get(reverse("finance:transactions"), {"month": "2026-11"})
        self.assertContains(listing, 'title="Recorded by the assistant" data-ai>AI</span>', count=1)

    def test_double_save(self):
        row = self.draft_card()
        url = reverse("assistant:save_draft", args=[row.pk])
        self.client.post(url, **HTMX)
        self.client.post(url, **HTMX)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_cancel(self):
        row = self.draft_card()
        self.assertContains(self.client.post(reverse("assistant:cancel_draft", args=[row.pk]), **HTMX), "Not saved")
        self.client.post(reverse("assistant:save_draft", args=[row.pk]), **HTMX)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_draft_no_longer_valid(self):
        row = self.draft_card()
        self.gopay.archive()
        self.assertContains(self.client.post(reverse("assistant:save_draft", args=[row.pk]), **HTMX), "Couldn't save")
        self.assertEqual(Transaction.objects.count(), 0)


class AssistantPrivacyTests(AssistantPageCase):
    def test_another_users_card(self):
        row = self.draft_card()
        other = make_user(email="other@example.com", name="Other")
        self.client.force_login(other)
        self.assertEqual(self.client.post(reverse("assistant:save_draft", args=[row.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("assistant:cancel_draft", args=[row.pk])).status_code, 404)
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertNotContains(self.client.get(PAGE), "Bakmi GM")

    def test_another_users_data(self):
        other = make_user(email="other@example.com", name="Other")
        wallet = Wallet.objects.create(user=other, name="Other BCA")
        self.add(9_000_000, user=other, wallet=wallet)
        self.add(50_000)
        self.script(Reply(tool_calls=[ToolCall("c1", "query_transactions", {"category": "Food & drinks"})]), Reply(text="Done."))
        response = self.ask("How much on food in November?")
        self.assertContains(response, "Rp50.000</dd>", html=False)
        self.assertNotContains(response, "Rp9.000.000")

    def test_requires_sign_in(self):
        self.client.logout()
        self.assertEqual(self.client.get(PAGE).status_code, 302)
        self.assertEqual(self.ask("Hi", htmx=False).status_code, 302)
        # From the page (HTMX), the browser is sent to sign-in as a full page (app-shell spec).
        response = self.ask("Hi")
        self.assertEqual(response.status_code, 204)
        self.assertTrue(response["HX-Redirect"].startswith("/sign-in/?next="))
