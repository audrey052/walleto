"""assistant spec: conversations and messages (add-assistant design decision 1)."""

from django.test import TestCase

from assistant.models import Conversation, Message
from finance.tests.test_views import make_user


class ConversationModelTests(TestCase):
    def test_a_conversation_belongs_to_one_user(self):
        mine, other = make_user(), make_user(email="other@example.com", name="Other")
        Conversation.objects.create(user=mine)
        Conversation.objects.create(user=other)
        self.assertEqual(Conversation.objects.for_user(mine).count(), 1)

    def test_messages_in_order_and_scoped(self):
        user, other = make_user(), make_user(email="other@example.com", name="Other")
        chat = Conversation.objects.create(user=user)
        Message.objects.create(conversation=chat, role=Message.Role.USER, text="first")
        Message.objects.create(conversation=chat, role=Message.Role.ASSISTANT, text="second")
        self.assertEqual([m.text for m in chat.messages.all()], ["first", "second"])
        self.assertEqual(Message.objects.for_user(other).count(), 0)

    def test_a_draft_card_keeps_its_state(self):
        chat = Conversation.objects.create(user=make_user())
        row = Message.objects.create(
            conversation=chat, role=Message.Role.TOOL, tool_name="add_transaction",
            cards=[{"type": "draft", "state": "pending", "fields": {"amount": 45000}}],
        )
        row.cards[0]["state"] = "saved"
        row.save()
        row.refresh_from_db()
        self.assertEqual(row.cards[0]["state"], "saved")
