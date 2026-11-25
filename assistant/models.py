"""Conversations with the Assistant (assistant spec, add-assistant design decision 1)."""

from django.conf import settings
from django.db import models
from django.utils import timezone


class ConversationQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)


class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    created_at = models.DateTimeField(default=timezone.now)

    objects = ConversationQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Conversation {self.pk} of {self.user}"


class MessageQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(conversation__user=user)


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        TOOL = "tool", "Tool"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=Role.choices)
    text = models.TextField(blank=True)
    # Tool rows keep the call and its result so later turns can replay them to the model.
    tool_call_id = models.CharField(max_length=100, blank=True)
    tool_name = models.CharField(max_length=50, blank=True)
    tool_args = models.JSONField(default=dict, blank=True)
    tool_result = models.JSONField(default=dict, blank=True)
    # Assistant rows: the calls the model made (replayed), the cards to show and the transaction count.
    tool_calls = models.JSONField(default=list, blank=True)
    cards = models.JSONField(default=list, blank=True)
    counted_transactions = models.PositiveIntegerField(default=0)
    # User rows: True when the question uses up the daily limit (design decision 6).
    counted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    objects = MessageQuerySet.as_manager()

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role}: {self.text[:40]}"
