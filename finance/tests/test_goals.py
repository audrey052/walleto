"""add-savings-goals: models, balances, calculations, forms, views, page, detail and privacy."""

import csv
from datetime import date, datetime, timezone as dt_timezone
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from finance import goals
from finance.forms import (
    CHOOSE_WALLET, DEADLINE_NOT_FUTURE, GOAL_NAME_USED, GOAL_TARGET_TOO_SMALL,
    DepositForm, GoalForm, WithdrawForm,
)

from finance.demo import build_demo
from finance.models import Category, GoalContribution, SavingsGoal, Transfer, Wallet

from .test_views import make_user

HTMX = {"HTTP_HX_REQUEST": "true"}
NOW = datetime(2026, 11, 18, 3, 0, tzinfo=dt_timezone.utc)  # 18 Nov 2026, 10:00 Jakarta
TODAY = date(2026, 11, 18)


class GoalTestCase(TestCase):
    def setUp(self):
        patcher = mock.patch("django.utils.timezone.now", return_value=NOW)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.user = make_user()
        self.client.force_login(self.user)
        self.bca = Wallet.objects.create(user=self.user, name="BCA", initial_balance=7_842_500)
        self.gopay = Wallet.objects.create(user=self.user, name="GoPay", type="ewallet", initial_balance=300_000)

    def goal(self, name="Bali trip", target=6_000_000, deadline=date(2027, 6, 30), start=TODAY, user=None, **extra):
        owner = user or self.user
        extra.setdefault("position", SavingsGoal.objects.filter(user=owner).count())  # appended, as the form does
        return SavingsGoal.objects.create(
            user=owner, name=name, target=target, deadline=deadline, start_date=start, **extra
        )

    def move(self, goal, wallet, amount, kind=GoalContribution.Kind.DEPOSIT, day=TODAY, note=""):
        return GoalContribution.objects.create(
            user=goal.user, goal=goal, wallet=wallet, kind=kind, amount=amount, date=day, note=note
        )

    def withdraw(self, goal, wallet, amount, day=TODAY):
        return self.move(goal, wallet, amount, kind=GoalContribution.Kind.WITHDRAWAL, day=day)

    def balance(self, wallet):
        return Wallet.objects.with_balance().get(pk=wallet.pk).balance

    def saved(self, goal):
        return SavingsGoal.objects.with_saved().get(pk=goal.pk).saved


class GoalBalanceTests(GoalTestCase):
    def test_balance_after_saving(self):
        # wallets spec, "Balance after saving": 7.842.500 - 1.000.000 + 400.000 = 7.242.500
        goal = self.goal()
        self.move(goal, self.bca, 1_000_000)
        self.withdraw(goal, self.bca, 400_000)
        self.assertEqual(self.balance(self.bca), 7_242_500)
        self.assertEqual(self.saved(goal), 600_000)

    def test_completed_and_deleted_goals_still_count(self):
        goal = self.goal(completed_at=NOW)
        self.move(goal, self.bca, 1_000_000)
        other = self.goal(name="Old", deleted_at=NOW)
        self.move(other, self.bca, 500_000)
        self.withdraw(other, self.gopay, 500_000)
        self.assertEqual(self.balance(self.bca), 6_342_500)
        self.assertEqual(self.balance(self.gopay), 800_000)

    def test_for_user_hides_deleted_goals(self):
        self.goal(name="Old", deleted_at=NOW)
        kept = self.goal()
        self.assertEqual(list(SavingsGoal.objects.for_user(self.user)), [kept])

    def test_transfer_overdraft_sees_goal_money(self):
        from finance.forms import TransferForm
        goal = self.goal()
        self.move(goal, self.gopay, 200_000)  # GoPay 300.000 -> 100.000
        form = TransferForm(
            {"from_wallet": self.gopay.pk, "to_wallet": self.bca.pk, "amount": "150.000", "date": "2026-11-18"},
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Not enough in GoPay", str(form.errors["amount"]))


class GoalCalculationTests(SimpleTestCase):
    """savings-goals spec scenarios with numbers."""

    def test_partway(self):
        self.assertEqual(goals.progress(1_500_000, 6_000_000), (25, 4_500_000))

    def test_percent_rounds_down(self):
        self.assertEqual(goals.progress(1_999_999, 6_000_000)[0], 33)

    def test_reached(self):
        self.assertEqual(goals.progress(6_000_000, 6_000_000), (100, 0))
        self.assertEqual(goals.progress(7_000_000, 6_000_000)[1], 0)

    def test_on_track(self):
        # 1 Sep to 30 Nov is 90 days; 18 Nov is 78 days in. 2.700.000 x 90 >= 3.000.000 x 78.
        start, deadline = date(2026, 9, 1), date(2026, 11, 30)
        self.assertEqual(goals.status(2_700_000, 3_000_000, start, deadline, TODAY), goals.ON_TRACK)

    def test_behind(self):
        start, deadline = date(2026, 9, 1), date(2026, 11, 30)
        # 2.500.000 x 90 < 3.000.000 x 78
        self.assertEqual(goals.status(2_500_000, 3_000_000, start, deadline, TODAY), goals.BEHIND)

    def test_exactly_on_the_line_is_on_track(self):
        start, deadline = date(2026, 11, 8), date(2026, 11, 28)  # 20 days, 10 elapsed
        self.assertEqual(goals.status(500_000, 1_000_000, start, deadline, TODAY), goals.ON_TRACK)
        self.assertEqual(goals.status(499_999, 1_000_000, start, deadline, TODAY), goals.BEHIND)

    def test_past_deadline(self):
        self.assertEqual(
            goals.status(100_000, 1_000_000, date(2026, 9, 1), date(2026, 10, 31), TODAY), goals.PAST_DEADLINE
        )

    def test_no_status_without_deadline_or_when_reached(self):
        self.assertIsNone(goals.status(0, 1_000_000, TODAY, None, TODAY))
        self.assertIsNone(goals.status(1_000_000, 1_000_000, date(2026, 9, 1), date(2026, 10, 1), TODAY))

    def test_per_month(self):
        # 18 Nov 2026 to 30 Jun 2027: November to June is 8 months; 6.000.000 / 8 = 750.000
        months = goals.months_left(TODAY, date(2027, 6, 30))
        self.assertEqual(months, 8)
        self.assertEqual(goals.per_month(6_000_000, months), 750_000)

    def test_per_month_rounds_up(self):
        self.assertEqual(goals.per_month(1_000_000, 3), 333_334)

    def test_deadline_this_month(self):
        self.assertEqual(goals.months_left(TODAY, date(2026, 11, 30)), 1)

    def _g(self, pk, position):
        return SimpleNamespace(pk=pk, position=position, created_at=pk)

    def test_main_goal_is_first_in_order(self):
        bali, laptop, fund = self._g(1, 2), self._g(2, 0), self._g(3, 1)
        self.assertIs(goals.main_goal([bali, laptop, fund]), laptop)

    def test_main_goal_ties_go_to_the_oldest(self):
        a, b = self._g(5, 0), self._g(4, 0)
        self.assertIs(goals.main_goal([a, b]), b)
        self.assertIsNone(goals.main_goal([]))

    def test_summary(self):
        goal = SimpleNamespace(target=6_000_000, start_date=TODAY, deadline=date(2027, 6, 30))
        summary = goals.summarize(goal, 1_500_000, TODAY)
        self.assertEqual((summary.percent, summary.to_go, summary.per_month), (25, 4_500_000, 562_500))
        self.assertEqual(summary.lines_filled, 2)  # round(0.25 x 9) = 2
        self.assertEqual(summary.status_label, "On track")
        reached = goals.summarize(goal, 6_000_000, TODAY)
        self.assertTrue(reached.reached)
        self.assertIsNone(reached.per_month)
        self.assertEqual(reached.lines_filled, 9)


class GoalSeriesTests(SimpleTestCase):
    def test_saved_steps_on_deposit_dates(self):
        start = date(2026, 11, 10)
        moves = [(date(2026, 11, 12), True, 1_000_000), (date(2026, 11, 15), True, 500_000)]
        series = goals.saved_series(start, date(2026, 11, 16), moves)
        self.assertEqual(series[0], (start, 0))
        self.assertEqual([s for _, s in series], [0, 0, 1_000_000, 1_000_000, 1_000_000, 1_500_000, 1_500_000])

    def test_withdrawal_steps_down(self):
        start = date(2026, 11, 10)
        moves = [(start, True, 1_000_000), (date(2026, 11, 11), False, 400_000)]
        self.assertEqual([s for _, s in goals.saved_series(start, date(2026, 11, 11), moves)], [1_000_000, 600_000])

    def test_plan_line(self):
        self.assertEqual(
            goals.plan_series(date(2026, 9, 1), date(2027, 6, 30), 6_000_000),
            [(date(2026, 9, 1), 0), (date(2027, 6, 30), 6_000_000)],
        )


class GoalFormTests(GoalTestCase):
    def form(self, data, instance=None):
        return GoalForm(data, user=self.user, instance=instance)

    def test_new_goal(self):
        form = self.form({"name": " Bali   trip ", "target": "6.000.000", "deadline": "2027-06-30"})
        self.assertTrue(form.is_valid(), form.errors)
        goal = form.save()
        self.assertEqual((goal.name, goal.target, goal.start_date), ("Bali trip", 6_000_000, TODAY))

    def test_deadline_must_be_after_today(self):
        for day in ("2026-11-18", "2026-10-01"):
            form = self.form({"name": "Bali trip", "target": "6.000.000", "deadline": day})
            self.assertEqual(form.errors["deadline"], [DEADLINE_NOT_FUTURE])

    def test_no_deadline(self):
        self.assertTrue(self.form({"name": "Emergency fund", "target": "10.000.000"}).is_valid())

    def test_duplicate_name_ignores_case(self):
        self.goal(name="Laptop")
        form = self.form({"name": "laptop", "target": "12.000.000"})
        self.assertEqual(form.errors["name"], [GOAL_NAME_USED])

    def test_name_free_again_after_completing_or_deleting(self):
        self.goal(name="Laptop", completed_at=NOW)
        self.goal(name="Bike", deleted_at=NOW)
        self.assertTrue(self.form({"name": "laptop", "target": "12.000.000"}).is_valid())
        self.assertTrue(self.form({"name": "Bike", "target": "12.000.000"}).is_valid())

    def test_target_minimum(self):
        self.assertEqual(self.form({"name": "Tiny", "target": "999"}).errors["target"], [GOAL_TARGET_TOO_SMALL])

    def test_edit_keeps_a_past_deadline(self):
        goal = self.goal(deadline=date(2026, 10, 31), start=date(2026, 9, 1))
        form = self.form({"name": "Bali trip", "target": "6.000.000", "deadline": "2026-10-31"}, instance=goal)
        self.assertTrue(form.is_valid(), form.errors)
        form = self.form({"name": "Bali trip", "target": "6.000.000", "deadline": "2026-11-01"}, instance=goal)
        self.assertEqual(form.errors["deadline"], [DEADLINE_NOT_FUTURE])


class MovementFormTests(GoalTestCase):
    def deposit(self, goal, **data):
        return DepositForm({"date": "2026-11-18", **data}, user=self.user, goal=goal)

    def test_deposit(self):
        goal = self.goal()
        form = self.deposit(goal, wallet=self.bca.pk, amount="1.000.000")
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(self.balance(self.bca), 6_842_500)
        self.assertEqual(self.saved(goal), 1_000_000)

    def test_not_enough_in_the_wallet(self):
        form = self.deposit(self.goal(), wallet=self.gopay.pk, amount="500.000")
        self.assertEqual(
            form.errors["amount"], ["Not enough in GoPay. Choose another wallet or a smaller amount."]
        )

    def test_exact_balance_is_fine(self):
        self.assertTrue(self.deposit(self.goal(), wallet=self.gopay.pk, amount="300.000").is_valid())

    def test_withdraw(self):
        goal = self.goal()
        self.move(goal, self.bca, 1_000_000)
        form = WithdrawForm(
            {"wallet": self.gopay.pk, "amount": "400.000", "date": "2026-11-18"}, user=self.user, goal=goal
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(self.saved(goal), 600_000)
        self.assertEqual(self.balance(self.gopay), 700_000)

    def test_withdraw_more_than_the_goal_holds(self):
        goal = self.goal()
        self.move(goal, self.bca, 600_000)
        form = WithdrawForm(
            {"wallet": self.gopay.pk, "amount": "700.000", "date": "2026-11-18"}, user=self.user, goal=goal
        )
        self.assertEqual(form.errors["amount"], ["This goal holds only Rp600.000."])

    def test_date_rules(self):
        goal = self.goal(start=date(2026, 11, 10))
        early = self.deposit(goal, wallet=self.bca.pk, amount="1.000", date="2026-11-09")
        self.assertEqual(early.errors["date"], ["The date can't be before this goal started (10 Nov 2026)."])
        future = self.deposit(goal, wallet=self.bca.pk, amount="1.000", date="2026-11-19")
        self.assertIn("date", future.errors)

    def test_archived_wallet_not_offered(self):
        self.gopay.is_archived = True
        self.gopay.save()
        form = self.deposit(self.goal(), wallet=self.gopay.pk, amount="1.000")
        self.assertEqual(form.errors["wallet"], [CHOOSE_WALLET])

    def test_another_users_wallet(self):
        other = make_user("other@example.com", "Other")
        theirs = Wallet.objects.create(user=other, name="Theirs", initial_balance=9_000_000)
        form = self.deposit(self.goal(), wallet=theirs.pk, amount="1.000")
        self.assertEqual(form.errors["wallet"], [CHOOSE_WALLET])


class GoalViewTests(GoalTestCase):
    """savings-goals spec: create, deposit, withdraw, main, complete, reopen, delete, movement delete."""

    def post(self, name, *args, data=None, htmx=True):
        return self.client.post(reverse(name, args=args), data or {}, **(HTMX if htmx else {}))

    def test_create(self):
        response = self.post("finance:goal_create", data={"name": "Bali trip", "target": "6.000.000", "deadline": "2027-06-30"})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["HX-Redirect"], reverse("finance:goals"))
        goal = SavingsGoal.objects.get(user=self.user)
        self.assertEqual((goal.name, goal.start_date), ("Bali trip", TODAY))
        page = self.client.get(reverse("finance:goals"))
        self.assertContains(page, "Goal created.")
        self.assertContains(page, "Bali trip")

    def test_create_shows_errors_in_the_modal(self):
        response = self.post("finance:goal_create", data={"name": "Bali trip", "target": "6.000.000", "deadline": "2026-11-18"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, DEADLINE_NOT_FUTURE)
        self.assertFalse(SavingsGoal.objects.exists())

    def test_deposit_and_withdraw(self):
        goal = self.goal()
        response = self.post("finance:goal_deposit", goal.pk, data={"wallet": self.bca.pk, "amount": "1.000.000", "date": "2026-11-18"})
        self.assertEqual(response.status_code, 204)
        self.assertContains(self.client.get(reverse("finance:goals")), "Added to Bali trip.")
        self.post("finance:goal_withdraw", goal.pk, data={"wallet": self.gopay.pk, "amount": "400.000", "date": "2026-11-18"})
        self.assertContains(self.client.get(reverse("finance:goals")), "Moved back to GoPay.")
        self.assertEqual(self.saved(goal), 600_000)
        self.assertEqual((self.balance(self.bca), self.balance(self.gopay)), (6_842_500, 700_000))

    def test_deposit_modal_lists_wallets_with_balances(self):
        goal = self.goal()
        response = self.client.get(reverse("finance:goal_deposit", args=[goal.pk]), **HTMX)
        self.assertContains(response, "BCA · Rp7.842.500")
        self.assertContains(response, "Add to this goal")

    def order(self, *goals_in_order):
        return self.client.post(reverse("finance:goal_reorder"), {"order": [g.pk for g in goals_in_order]})

    def page_order(self):
        page = self.client.get(reverse("finance:goals"))
        return [page.context["main"].goal.name] + [s.goal.name for s in page.context["others"]]

    def test_reorder_sets_the_main_goal(self):
        laptop = self.goal(name="Laptop", deadline=date(2027, 3, 31))
        fund = self.goal(name="Emergency fund", deadline=None)
        bali = self.goal(name="Bali trip")
        self.assertEqual(self.page_order(), ["Laptop", "Emergency fund", "Bali trip"])
        self.assertEqual(self.order(fund, bali, laptop).status_code, 204)
        self.assertEqual(self.page_order(), ["Emergency fund", "Bali trip", "Laptop"])

    def test_reorder_keeps_unlisted_goals_after_the_listed_ones(self):
        a, b, c = self.goal(name="A"), self.goal(name="B"), self.goal(name="C")
        self.order(c)
        self.assertEqual(self.page_order(), ["C", "A", "B"])

    def test_reorder_needs_post(self):
        self.assertEqual(self.client.get(reverse("finance:goal_reorder")).status_code, 405)

    def test_new_goal_goes_last(self):
        self.goal(name="Laptop")
        self.post("finance:goal_create", data={"name": "Bali trip", "target": "6.000.000"})
        self.assertEqual(self.page_order(), ["Laptop", "Bali trip"])

    def test_reopened_goal_goes_last(self):
        done = self.goal(name="Bike", target=1_000, completed_at=NOW)
        self.goal(name="Laptop")
        self.post("finance:goal_reopen", done.pk, htmx=False)
        self.assertEqual(self.page_order(), ["Laptop", "Bike"])

    def test_no_make_main_button_and_handles_only_with_two_goals(self):
        goal = self.goal(name="Laptop")
        page = self.client.get(reverse("finance:goals"))
        self.assertNotContains(page, "Make main goal")
        self.assertNotContains(page, "drag-handle")
        self.assertNotContains(self.client.get(reverse("finance:goal_detail", args=[goal.pk])), "Make main goal")
        self.goal(name="Bali trip")
        page = self.client.get(reverse("finance:goals"))
        self.assertContains(page, "drag-handle", count=2)
        self.assertContains(page, "vendor/sortable.min.js")

    def test_complete_only_when_reached(self):
        goal = self.goal(target=1_000_000)
        self.move(goal, self.bca, 400_000)
        self.post("finance:goal_complete", goal.pk, htmx=False)
        goal.refresh_from_db()
        self.assertIsNone(goal.completed_at)
        self.move(goal, self.bca, 600_000)
        self.post("finance:goal_complete", goal.pk, htmx=False)
        goal.refresh_from_db()
        self.assertIsNotNone(goal.completed_at)
        # The money counts as used: wallets stay where they were.
        self.assertEqual(self.balance(self.bca), 6_842_500)

    def test_completed_goal_takes_no_money_and_can_reopen(self):
        goal = self.goal(completed_at=NOW)
        response = self.client.get(reverse("finance:goal_deposit", args=[goal.pk]), **HTMX)
        self.assertEqual(response.status_code, 404)
        self.post("finance:goal_reopen", goal.pk, htmx=False)
        goal.refresh_from_db()
        self.assertIsNone(goal.completed_at)

    def test_delete_an_empty_goal_keeps_wallet_balances(self):
        # spec, "Delete an empty goal": in from BCA, out to GoPay, then delete.
        goal = self.goal()
        self.move(goal, self.bca, 500_000)
        self.withdraw(goal, self.gopay, 500_000)
        before = (self.balance(self.bca), self.balance(self.gopay))
        response = self.post("finance:goal_delete", goal.pk)
        self.assertEqual(response.status_code, 204)
        self.assertEqual((self.balance(self.bca), self.balance(self.gopay)), before)
        self.assertFalse(SavingsGoal.objects.for_user(self.user).exists())
        self.assertEqual(GoalContribution.objects.filter(goal=goal).count(), 2)
        self.assertContains(self.client.get(reverse("finance:goals")), "Goal deleted.")

    def test_delete_a_goal_that_holds_money(self):
        goal = self.goal()
        self.move(goal, self.bca, 600_000)
        confirm = self.client.get(reverse("finance:goal_delete", args=[goal.pk]), **HTMX)
        self.assertContains(confirm, "Move the money back first")
        self.assertContains(confirm, reverse("finance:goal_withdraw", args=[goal.pk]))
        self.assertNotContains(confirm, "Delete goal</button>")
        self.post("finance:goal_delete", goal.pk)
        goal.refresh_from_db()
        self.assertIsNone(goal.deleted_at)

    def test_delete_a_deposit(self):
        goal = self.goal()
        deposit = self.move(goal, self.bca, 1_000_000)
        self.post("finance:goal_movement_delete", deposit.pk)
        self.assertEqual(self.saved(goal), 0)
        self.assertEqual(self.balance(self.bca), 7_842_500)

    def test_deleting_a_deposit_cant_make_saved_negative(self):
        goal = self.goal()
        deposit = self.move(goal, self.bca, 1_000_000)
        self.withdraw(goal, self.gopay, 800_000)
        self.post("finance:goal_movement_delete", deposit.pk)
        self.assertTrue(GoalContribution.objects.filter(pk=deposit.pk).exists())
        self.assertEqual(self.saved(goal), 200_000)

    def test_section_is_active(self):
        response = self.client.get(reverse("finance:goals"))
        self.assertEqual(response.context["active_section"]["key"], "savings")
        goal = self.goal()
        detail = self.client.get(reverse("finance:goal_detail", args=[goal.pk]))
        self.assertEqual(detail.context["active_section"]["key"], "savings")


class GoalPageTests(GoalTestCase):
    def page(self):
        return self.client.get(reverse("finance:goals"))

    def test_no_goals(self):
        response = self.page()
        self.assertContains(response, "Create a goal")
        # One create button only: the heading's "New goal" appears once a goal exists.
        self.assertNotContains(response, "New goal")
        self.goal()
        self.assertContains(self.page(), "New goal")
        self.assertIsNone(response.context["main"])
        self.assertContains(response, '<div id="modal-root"></div>', html=True)

    def test_several_goals(self):
        self.goal(name="Bali trip", deadline=date(2027, 6, 30))
        self.goal(name="Emergency fund", deadline=None)
        self.goal(name="Laptop", deadline=date(2027, 3, 31))
        response = self.page()
        self.assertEqual(response.context["main"].goal.name, "Bali trip")
        self.assertEqual([s.goal.name for s in response.context["others"]], ["Emergency fund", "Laptop"])
        self.assertNotContains(response, "Other goals")
        self.assertContains(response, '<div id="modal-root"></div>', html=True)

    def test_main_card_figures(self):
        goal = self.goal()
        self.move(goal, self.bca, 1_500_000)
        response = self.page()
        self.assertContains(response, "25% of the way there")
        self.assertContains(response, "Rp4.500.000 to go")
        self.assertContains(response, "Add to this goal")
        # 4.500.000 over November to June (8 months) = 562.500
        self.assertContains(response, "Rp562.500 a month")
        self.assertContains(response, "to reach your target by June 2027.")
        self.assertEqual(response.context["main"].status, "on_track")
        self.assertNotContains(response, "On track")  # no label for an on-track goal

    def test_main_card_opens_the_goal(self):
        # The whole card links to the detail page, where Edit lives; no separate links on the card.
        goal = self.goal()
        response = self.page()
        self.assertContains(response, f'href="{reverse("finance:goal_detail", args=[goal.pk])}" class="absolute inset-0')
        self.assertNotContains(response, "Edit goal")
        self.assertNotContains(response, "View history")
        self.assertNotContains(response, reverse("finance:goal_edit", args=[goal.pk]))

    def test_reached(self):
        goal = self.goal(target=1_000_000)
        self.move(goal, self.bca, 1_000_000)
        response = self.page()
        self.assertContains(response, "Your goal, reached.")
        self.assertContains(response, "Mark as complete")
        self.assertNotContains(response, "a month to reach")

    def test_completed_section(self):
        self.goal(name="Laptop", completed_at=NOW)
        response = self.page()
        self.assertContains(response, "Completed")
        self.assertContains(response, "Reopen")
        self.assertContains(response, "Create a goal")
        self.assertNotContains(response, "New goal")

    def test_goal_without_deadline_has_no_status_or_monthly_amount(self):
        self.goal(name="Emergency fund", deadline=None)
        response = self.page()
        self.assertContains(response, "No deadline")
        self.assertNotContains(response, "a month to reach")
        self.assertNotContains(response, "On track")


class GoalDetailTests(GoalTestCase):
    def test_history_newest_first_and_chart_data(self):
        goal = self.goal(start=date(2026, 11, 10), deadline=date(2027, 6, 30))
        self.move(goal, self.bca, 1_000_000, day=date(2026, 11, 12))
        self.withdraw(goal, self.gopay, 400_000, day=date(2026, 11, 15))
        response = self.client.get(reverse("finance:goal_detail", args=[goal.pk]))
        content = response.content.decode()
        self.assertLess(content.index("To GoPay"), content.index("From BCA"))
        self.assertContains(response, "+Rp1.000.000")
        self.assertContains(response, "−Rp400.000")
        chart = response.context["chart"]
        self.assertEqual(chart["saved"][0], ["2026-11-10", 0])
        self.assertEqual(chart["saved"][-1], ["2026-11-18", 600_000])
        self.assertEqual(chart["plan"], [["2026-11-10", 0], ["2027-06-30", 6_000_000]])
        self.assertContains(response, 'id="goal-chart-data"')
        self.assertContains(response, "vendor/apexcharts.min.js")
        self.assertContains(response, '<div id="modal-root"></div>', html=True)

    def test_no_plan_without_deadline(self):
        goal = self.goal(deadline=None)
        response = self.client.get(reverse("finance:goal_detail", args=[goal.pk]))
        self.assertIsNone(response.context["chart"]["plan"])

    def test_chart_script_only_on_the_detail_page(self):
        self.goal()
        for name in ("finance:goals", "finance:wallets", "finance:budget", "finance:transactions"):
            self.assertNotContains(self.client.get(reverse(name)), "apexcharts")


class GoalPrivacyTests(GoalTestCase):
    """savings-goals spec, "Goals are private"."""

    def setUp(self):
        super().setUp()
        self.other = make_user("other@example.com", "Other")
        self.their_wallet = Wallet.objects.create(user=self.other, name="Theirs", initial_balance=9_000_000)
        self.theirs = self.goal(name="Their goal", user=self.other)
        self.their_move = self.move(self.theirs, self.their_wallet, 1_000_000)

    def test_another_users_goal_is_not_found(self):
        for name in ("finance:goal_detail", "finance:goal_edit", "finance:goal_deposit", "finance:goal_withdraw", "finance:goal_delete"):
            self.assertEqual(self.client.get(reverse(name, args=[self.theirs.pk])).status_code, 404, name)
        for name in ("finance:goal_complete", "finance:goal_reopen"):
            self.assertEqual(self.client.post(reverse(name, args=[self.theirs.pk])).status_code, 404, name)

    def test_reorder_ignores_another_users_goals(self):
        mine = self.goal()
        self.client.post(reverse("finance:goal_reorder"), {"order": [self.theirs.pk, mine.pk]})
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.position, 0)
        mine.refresh_from_db()
        self.assertEqual(mine.position, 0)

    def test_another_users_movement_is_not_found(self):
        url = reverse("finance:goal_movement_delete", args=[self.their_move.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(GoalContribution.objects.filter(pk=self.their_move.pk).exists())

    def test_page_lists_only_own_goals(self):
        mine = self.goal()
        response = self.client.get(reverse("finance:goals"))
        self.assertEqual(response.context["main"].goal, mine)
        self.assertNotContains(response, "Their goal")

    def test_deposit_with_another_users_wallet(self):
        goal = self.goal()
        response = self.client.post(
            reverse("finance:goal_deposit", args=[goal.pk]),
            {"wallet": self.their_wallet.pk, "amount": "1.000", "date": "2026-11-18"}, **HTMX,
        )
        self.assertContains(response, CHOOSE_WALLET)
        self.assertEqual(self.saved(goal), 0)

    def test_deleted_goal_is_not_found(self):
        goal = self.goal(deleted_at=NOW)
        self.assertEqual(self.client.get(reverse("finance:goal_detail", args=[goal.pk])).status_code, 404)


class GoalWalletsAndActivityTests(GoalTestCase):
    """wallets spec, "Money set aside in goals"; transactions spec, goal movements in the list and CSV."""

    def test_set_aside_on_the_wallets_page(self):
        goal = self.goal()
        self.move(goal, self.bca, 1_000_000)
        other = self.goal(name="Laptop")
        self.move(other, self.gopay, 100_000)
        done = self.goal(name="Bike", completed_at=NOW)
        self.move(done, self.bca, 500_000)
        response = self.client.get(reverse("finance:wallets"))
        self.assertEqual(response.context["set_aside"], 1_100_000)
        self.assertContains(response, "Set aside in goals")
        self.assertContains(response, "Rp1.100.000")
        # Total stays spendable money: 7.842.500 - 1.000.000 - 500.000 + 300.000 - 100.000
        self.assertEqual(response.context["total_balance"], 6_542_500)

    def test_nothing_set_aside(self):
        self.goal()
        self.assertNotContains(self.client.get(reverse("finance:wallets")), "Set aside in goals")

    def test_deposit_in_the_list(self):
        goal = self.goal()
        self.move(goal, self.bca, 1_000_000)
        response = self.client.get(reverse("finance:transactions"))
        self.assertContains(response, "BCA → Bali trip")
        self.assertContains(response, "Savings goal")
        self.assertContains(response, reverse("finance:goal_detail", args=[goal.pk]))
        self.assertEqual(response.context["entry_count"], 1)
        self.assertEqual(response.context["summary"]["expense"], 0)

    def test_withdrawal_route(self):
        goal = self.goal()
        self.move(goal, self.bca, 1_000_000)
        self.withdraw(goal, self.gopay, 400_000)
        self.assertContains(self.client.get(reverse("finance:transactions")), "Bali trip → GoPay")

    def test_filters(self):
        goal = self.goal()
        self.move(goal, self.bca, 1_000_000)
        url = reverse("finance:transactions")
        self.assertContains(self.client.get(url, {"wallet": self.bca.pk}), "BCA → Bali trip")
        self.assertNotContains(self.client.get(url, {"wallet": self.gopay.pk}), "BCA → Bali trip")
        food = Category.objects.get(user=None, name="Food & drinks")
        self.assertNotContains(self.client.get(url, {"category": food.pk}), "BCA → Bali trip")
        self.assertContains(self.client.get(url, {"q": "bali"}), "BCA → Bali trip")

    def test_deleted_goal_row_has_no_link(self):
        goal = self.goal()
        self.move(goal, self.bca, 500_000)
        self.withdraw(goal, self.bca, 500_000)
        SavingsGoal.objects.filter(pk=goal.pk).update(deleted_at=NOW)
        response = self.client.get(reverse("finance:transactions"))
        self.assertContains(response, "BCA → Bali trip")
        self.assertNotContains(response, reverse("finance:goal_detail", args=[goal.pk]))

    def test_export_a_deposit(self):
        goal = self.goal()
        self.move(goal, self.bca, 1_000_000)
        response = self.client.get(reverse("finance:transactions_export"), {"month": "2026-11"})
        rows = list(csv.reader(response.content.decode("utf-8-sig").splitlines()))
        self.assertIn(["2026-11-18", "Savings", "BCA → Bali trip", "", "Savings goal", "BCA", "1000000"], rows)


class DemoGoalTests(TestCase):
    """demo-account spec, "Demo savings goals"."""

    def test_goals_with_history_and_something_to_notice(self):
        today = date(2026, 11, 18)
        user = build_demo(today)
        active = list(SavingsGoal.objects.for_user(user).active().with_saved())
        self.assertGreaterEqual(len(active), 2)
        statuses = set()
        for goal in active:
            moves = GoalContribution.objects.filter(goal=goal)
            self.assertTrue(moves.exists())
            self.assertGreaterEqual(moves.earliest("date").date, date(2026, 9, 1))
            self.assertLessEqual(moves.latest("date").date, today)
            statuses.add(goals.summarize(goal, goal.saved, today).status)
        self.assertEqual(statuses, {goals.ON_TRACK, goals.BEHIND})
        balances = Wallet.objects.for_user(user).with_balance().values_list("balance", flat=True)
        self.assertTrue(all(b >= 0 for b in balances))

    def test_statuses_hold_on_other_dates(self):
        for today in (date(2026, 11, 2), date(2027, 1, 31), date(2027, 3, 15)):
            user = build_demo(today)
            statuses = {
                goals.summarize(g, g.saved, today).status
                for g in SavingsGoal.objects.for_user(user).active().with_saved()
            }
            self.assertEqual(statuses, {goals.ON_TRACK, goals.BEHIND}, today)

    def test_reset_keeps_others_goals(self):
        other = make_user("other@example.com", "Other")
        wallet = Wallet.objects.create(user=other, name="Mine", initial_balance=1_000_000)
        theirs = SavingsGoal.objects.create(user=other, name="Bike", target=2_000_000, start_date=date(2026, 11, 1))
        GoalContribution.objects.create(user=other, goal=theirs, wallet=wallet, kind="deposit", amount=100_000, date=date(2026, 11, 2))
        build_demo(date(2026, 11, 18))
        build_demo(date(2026, 11, 18))
        self.assertEqual(GoalContribution.objects.filter(user=other).count(), 1)
        self.assertTrue(SavingsGoal.objects.filter(pk=theirs.pk).exists())
