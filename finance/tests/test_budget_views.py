"""Budgets spec (page, modals, privacy) and the transactions budget warning."""

from datetime import date, datetime, timezone as dt_timezone
from unittest import mock

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from finance.models import Budget, Category, Transaction, Wallet

from .test_views import make_user

HTMX = {"HTTP_HX_REQUEST": "true"}
# Freeze "today" at 17 Nov 2026, 10:00 in Jakarta (03:00 UTC).
NOW = datetime(2026, 11, 17, 3, 0, tzinfo=dt_timezone.utc)
NOV, OCT, DEC = date(2026, 11, 1), date(2026, 10, 1), date(2026, 12, 1)


def cat(name):
    return Category.objects.get(user=None, name=name)


class BudgetViewTestCase(TestCase):
    def setUp(self):
        patcher = mock.patch("django.utils.timezone.now", return_value=NOW)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.user = make_user()
        self.client.force_login(self.user)
        self.bca = Wallet.objects.create(user=self.user, name="BCA", initial_balance=50_000_000)
        self.food, self.transport, self.health = cat("Food & drinks"), cat("Transport"), cat("Health")
        self.page = reverse("finance:budget")

    def url(self, name, *args, month="2026-11"):
        return f"{reverse(name, args=args)}?month={month}"

    def limit(self, category, amount, month=NOV, user=None):
        return Budget.objects.create(user=user or self.user, category=category, month=month, limit=amount)

    def spend(self, amount, category=None, day=date(2026, 11, 10)):
        return Transaction.objects.create(
            user=self.user, wallet=self.bca, category=category or self.food,
            amount=amount, date=day, description="Test",
        )

    def limits(self, month=NOV, user=None):
        return dict(
            Budget.objects.filter(user=user or self.user, month=month).values_list("category__name", "limit")
        )

    def toasts(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]


class BudgetPageTests(BudgetViewTestCase):
    def test_modal_target_present_with_and_without_plan(self):
        # Every hx-target="#modal-root" link needs the element on the page, or the modal never opens.
        self.assertContains(self.client.get(self.page), '<div id="modal-root"></div>', html=True)
        self.limit(self.food, 2_400_000)
        self.assertContains(self.client.get(self.page), '<div id="modal-root"></div>', html=True)

    def test_empty_state_without_copy(self):
        response = self.client.get(self.page)
        self.assertContains(response, "Set monthly plan")
        self.assertNotContains(response, "Copy last month")
        self.assertNotContains(response, "Edit monthly plan")

    def test_empty_state_offers_copy_when_last_month_has_limits(self):
        self.limit(self.food, 3_000_000, month=OCT)
        response = self.client.get(self.page)
        self.assertContains(response, "Copy last month's budget")

    def test_page_shows_plan_rows_and_unbudgeted(self):
        self.limit(self.food, 2_400_000)
        self.limit(self.transport, 1_600_000)
        self.spend(2_147_500)
        self.spend(1_700_000, self.transport)
        self.spend(300_000, self.health)
        response = self.client.get(self.page)
        plan = response.context["plan"]
        self.assertEqual(plan.plan, 4_000_000)
        self.assertEqual(plan.spent, 4_147_500)
        self.assertContains(response, "Edit monthly plan")
        self.assertContains(response, "A place for every Rupiah")
        self.assertContains(response, "Rp2.147.500")
        self.assertContains(response, "of Rp2.400.000")
        self.assertContains(response, "89%")
        self.assertContains(response, "Getting close to your limit")
        self.assertContains(response, "Over by Rp100.000")
        self.assertContains(response, "No limit set · Rp300.000 spent")
        self.assertContains(response, "Rp147.500 over plan")
        self.assertContains(response, "14 days left")

    def test_per_day(self):
        self.limit(self.food, 3_000_000)
        self.spend(200_000)
        self.assertContains(self.client.get(self.page), "14 days left · Rp200.000 a day")

    def test_month_handling(self):
        self.assertEqual(self.client.get(self.page).context["month_start"], NOV)
        response = self.client.get(f"{self.page}?month=2026-12")
        self.assertEqual(response.context["month_start"], DEC)
        self.assertIsNone(response.context["next_url"])
        for bad in ("2026-13", "2027-01", "nope"):
            with self.subTest(month=bad):
                self.assertEqual(self.client.get(f"{self.page}?month={bad}").context["month_start"], NOV)

    def test_past_month_shows_no_days_left(self):
        self.limit(self.food, 3_000_000, month=OCT)
        response = self.client.get(f"{self.page}?month=2026-10")
        self.assertEqual(response.context["plan"].days_left, 0)
        self.assertNotContains(response, "days left")

    def test_sidebar_marks_budget_active(self):
        response = self.client.get(self.page)
        self.assertEqual(response.context["active_section"]["key"], "budget")


class PlanModalTests(BudgetViewTestCase):
    def test_modal(self):
        response = self.client.get(self.url("finance:budget_plan"), **HTMX)
        self.assertContains(response, "Give your month a plan.")
        self.assertContains(response, "Your category limits will adjust proportionally.")

    def test_first_split(self):
        response = self.client.post(self.url("finance:budget_plan"), {"total": "8.000.000"})
        self.assertRedirects(response, self.url("finance:budget"))
        limits = self.limits()
        self.assertEqual(limits["Food & drinks"], 2_400_000)
        self.assertEqual(sum(limits.values()), 8_000_000)
        self.assertIn("Your monthly spending plan has been updated.", self.toasts(response))

    def test_rescale_keeps_unbudgeted_empty(self):
        self.limit(self.food, 3_000_000)
        self.limit(self.transport, 1_000_000)
        self.client.post(self.url("finance:budget_plan"), {"total": "6.000.000"})
        self.assertEqual(self.limits(), {"Food & drinks": 4_500_000, "Transport": 1_500_000})

    def test_plan_for_next_month(self):
        self.client.post(self.url("finance:budget_plan", month="2026-12"), {"total": "8.000.000"})
        self.assertEqual(sum(self.limits(DEC).values()), 8_000_000)

    def test_htmx_save_redirects(self):
        response = self.client.post(self.url("finance:budget_plan"), {"total": "8.000.000"}, **HTMX)
        self.assertEqual(response["HX-Redirect"], self.url("finance:budget"))

    def test_too_small(self):
        response = self.client.post(self.url("finance:budget_plan"), {"total": "50.000"})
        self.assertContains(response, "The plan must be at least Rp100.000.")
        self.assertFalse(Budget.objects.exists())

    def test_rescale_that_would_drop_a_limit_below_minimum(self):
        self.limit(self.food, 50_000_000)
        self.limit(self.health, 1_000)
        response = self.client.post(self.url("finance:budget_plan"), {"total": "100.000"})
        self.assertContains(response, "smaller than Rp1.000")
        self.assertEqual(self.limits()["Food & drinks"], 50_000_000)


class CategoryLimitTests(BudgetViewTestCase):
    def test_set_change_and_remove(self):
        url = self.url("finance:budget_category", self.food.pk)
        response = self.client.post(url, {"limit": "3.000.000"})
        self.assertIn("Food & drinks budget updated.", self.toasts(response))
        self.client.post(url, {"limit": "2.500.000"})
        self.assertEqual(self.limits(), {"Food & drinks": 2_500_000})

        remove = self.url("finance:budget_category_remove", self.food.pk)
        self.assertContains(self.client.get(remove), "Remove the Food &amp; drinks limit?")
        self.assertEqual(self.limits(), {"Food & drinks": 2_500_000})  # GET only asks
        response = self.client.post(remove)
        self.assertIn("Food & drinks limit removed.", self.toasts(response))
        self.assertEqual(self.limits(), {})

    def test_edit_modal_offers_remove(self):
        self.limit(self.food, 3_000_000)
        response = self.client.get(self.url("finance:budget_category", self.food.pk), **HTMX)
        self.assertContains(response, "Edit budget")
        self.assertContains(response, "Remove limit")

    def test_too_small(self):
        response = self.client.post(self.url("finance:budget_category", self.food.pk), {"limit": "500"})
        self.assertContains(response, "The limit must be at least Rp1.000.")
        self.assertFalse(Budget.objects.exists())

    def test_income_category_is_not_found(self):
        response = self.client.post(self.url("finance:budget_category", cat("Salary").pk), {"limit": "1.000.000"})
        self.assertEqual(response.status_code, 404)


class CopyTests(BudgetViewTestCase):
    def test_copy_last_month(self):
        self.limit(self.food, 3_000_000, month=OCT)
        self.limit(self.transport, 1_000_000, month=OCT)
        response = self.client.post(self.url("finance:budget_copy"))
        self.assertEqual(self.limits(), {"Food & drinks": 3_000_000, "Transport": 1_000_000})
        self.assertIn("Copied October's budget.", self.toasts(response))

    def test_get_does_nothing(self):
        self.limit(self.food, 3_000_000, month=OCT)
        response = self.client.get(self.url("finance:budget_copy"))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.limits(), {})

    def test_never_overwrites(self):
        self.limit(self.food, 3_000_000, month=OCT)
        self.limit(self.food, 2_000_000)
        self.client.post(self.url("finance:budget_copy"))
        self.assertEqual(self.limits(), {"Food & drinks": 2_000_000})

    def test_nothing_to_copy(self):
        self.client.post(self.url("finance:budget_copy"))
        self.assertFalse(Budget.objects.exists())


class BudgetPrivacyTests(BudgetViewTestCase):
    def setUp(self):
        super().setUp()
        self.other = make_user("sari@example.com", "Sari Wulandari")
        self.their_food = self.limit(self.food, 9_000_000, user=self.other)
        self.limit(self.food, 9_000_000, month=OCT, user=self.other)

    def test_page_shows_only_own_limits(self):
        response = self.client.get(self.page)
        self.assertFalse(response.context["plan"].has_plan)
        self.assertNotContains(response, "Copy last month")

    def test_plan_creates_separate_limits(self):
        self.client.post(self.url("finance:budget_plan"), {"total": "8.000.000"})
        self.assertEqual(self.limits(user=self.other), {"Food & drinks": 9_000_000})
        self.assertEqual(self.limits()["Food & drinks"], 2_400_000)

    def test_edit_remove_and_copy_never_touch_other_users(self):
        self.client.post(self.url("finance:budget_category", self.food.pk), {"limit": "1.000.000"})
        self.client.post(self.url("finance:budget_category_remove", self.food.pk))
        self.client.post(self.url("finance:budget_copy"))
        self.their_food.refresh_from_db()
        self.assertEqual(self.their_food.limit, 9_000_000)
        self.assertEqual(self.limits(), {})

    def test_remove_without_own_limit_is_not_found(self):
        self.assertEqual(self.client.get(self.url("finance:budget_category_remove", self.food.pk)).status_code, 404)

    def test_other_users_category_is_not_found(self):
        theirs = Category.objects.create(user=self.other, name="Pets", kind="expense", color="#1F5C4A")
        response = self.client.post(self.url("finance:budget_category", theirs.pk), {"limit": "100.000"})
        self.assertEqual(response.status_code, 404)


class TransactionBudgetWarningTests(BudgetViewTestCase):
    def add(self, amount, category=None, day="2026-11-17"):
        return self.client.post(reverse("finance:transaction_create"), {
            "description": "GoFood", "amount": str(amount), "category": (category or self.food).pk,
            "wallet": self.bca.pk, "date": day, "note": "",
        })

    def test_crossing_85_percent(self):
        self.limit(self.food, 2_400_000)
        self.spend(2_000_000)
        response = self.add(100_000)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            [str(m) for m in messages],
            ["Transaction added.", "Food & drinks is at 87% of its November budget."],
        )
        self.assertEqual(messages[1].level_tag, "warning")
        self.assertEqual(messages[1].extra_tags, f"{self.page}?month=2026-11")

    def test_going_over(self):
        self.limit(self.food, 2_400_000)
        self.spend(2_350_000)
        response = self.add(100_000)
        self.assertIn("Food & drinks is over its November budget by Rp50.000.", self.toasts(response))

    def test_already_in_warning(self):
        self.limit(self.food, 2_400_000)
        self.spend(2_160_000)
        self.assertEqual(self.toasts(self.add(24_000)), ["Transaction added."])

    def test_no_plan(self):
        self.spend(2_000_000)
        self.assertEqual(self.toasts(self.add(100_000)), ["Transaction added."])

    def test_category_without_limit(self):
        self.limit(self.food, 2_400_000)
        self.assertEqual(self.toasts(self.add(500_000, self.health)), ["Transaction added."])

    def test_income(self):
        self.limit(self.food, 2_400_000)
        self.assertEqual(self.toasts(self.add(12_500_000, cat("Salary"))), ["Transaction added."])

    def test_edit_into_another_category(self):
        shopping = cat("Shopping")
        self.limit(shopping, 1_000_000)
        self.spend(800_000, shopping)
        record = self.spend(150_000, self.food)
        response = self.client.post(reverse("finance:transaction_edit", args=[record.pk]), {
            "description": "Uniqlo", "amount": "150.000", "category": shopping.pk,
            "wallet": self.bca.pk, "date": "2026-11-10", "note": "",
        })
        self.assertIn("Shopping is at 95% of its November budget.", self.toasts(response))
