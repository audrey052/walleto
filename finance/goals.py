"""Savings goal calculations (savings-goals spec; add-savings-goals design decision 4).

Pure functions over whole Rupiah and dates. No floats: status compares by
cross-multiplication, and the monthly amount is rounded up with integer division.
"""

from dataclasses import dataclass
from datetime import timedelta

ON_TRACK = "on_track"
BEHIND = "behind"
PAST_DEADLINE = "past_deadline"
STATUS_LABELS = {ON_TRACK: "On track", BEHIND: "Behind", PAST_DEADLINE: "Past deadline"}

LEDGER_LINES = 9  # Figma `.savings-lines`
LEDGER_HEIGHTS = [22, 31, 41, 51, 61, 71, 81, 91, 100]  # percent, Figma `.savings-lines > div:nth-child(n)`


def progress(saved, target):
    """(percent rounded down, amount to go never below Rp0)."""
    percent = max(saved, 0) * 100 // target
    return percent, max(target - saved, 0)


def status(saved, target, start, deadline, today):
    """ON_TRACK / BEHIND / PAST_DEADLINE, or None without a deadline or once reached."""
    if deadline is None or saved >= target:
        return None
    if today > deadline:
        return PAST_DEADLINE
    total = (deadline - start).days
    elapsed = min(max((today - start).days, 0), total)
    if total <= 0:
        return BEHIND
    return ON_TRACK if saved * total >= target * elapsed else BEHIND


def months_left(today, deadline):
    """Months from today's month to the deadline's month, both counted."""
    return (deadline.year - today.year) * 12 + deadline.month - today.month + 1


def per_month(to_go, months):
    """Amount needed each month, rounded up to the next Rupiah."""
    return -(-to_go // max(months, 1))


def main_goal(goals):
    """The goal made main, else the nearest deadline, else the oldest goal without one."""
    goals = list(goals)
    if not goals:
        return None
    chosen = [g for g in goals if g.is_main]
    if chosen:
        return chosen[0]
    dated = [g for g in goals if g.deadline]
    if dated:
        return min(dated, key=lambda g: (g.deadline, g.created_at, g.pk))
    return min(goals, key=lambda g: (g.created_at, g.pk))


def saved_series(start, today, movements):
    """[(day, saved at the end of that day)] from `start` to `today`.

    `movements` are (date, is_deposit, amount) tuples.
    """
    change = {}
    for day, is_deposit, amount in movements:
        change[day] = change.get(day, 0) + (amount if is_deposit else -amount)
    saved = sum(v for d, v in change.items() if d < start)
    series = []
    day = start
    while day <= today:
        saved += change.get(day, 0)
        series.append((day, saved))
        day += timedelta(days=1)
    return series


def plan_series(start, deadline, target):
    """The straight plan line: Rp0 on the start date, the target on the deadline."""
    return [(start, 0), (deadline, target)]


@dataclass
class GoalSummary:
    goal: object
    saved: int
    percent: int
    to_go: int
    reached: bool
    status: str | None
    months_left: int | None
    per_month: int | None
    lines_filled: int

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, "")


def summarize(goal, saved, today):
    """Every figure a goal shows on the page, the detail page and the card."""
    percent, to_go = progress(saved, goal.target)
    reached = saved >= goal.target
    goal_status = status(saved, goal.target, goal.start_date, goal.deadline, today)
    months = per = None
    if goal.deadline and not reached and goal_status != PAST_DEADLINE:
        months = months_left(today, goal.deadline)
        per = per_month(to_go, months)
    # Figma: round(min(1, saved / target) * 9), done with integers (round half up).
    capped = min(max(saved, 0), goal.target)
    filled = (capped * LEDGER_LINES * 2 + goal.target) // (goal.target * 2)
    return GoalSummary(goal, saved, percent, to_go, reached, goal_status, months, per, filled)
