"""The period a page covers: a whole month or a range of days (period-picker spec,
add-date-range design decision 1).

A whole month keeps the `?month=YYYY-MM` address so old links still work; any
other range uses `?from=YYYY-MM-DD&to=YYYY-MM-DD`, both days included.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

from .months import month_param, parse_month, shift

MAX_DAYS = 92


def _last_day(year, month):
    return date(year, month, calendar.monthrange(year, month)[1])


@dataclass(frozen=True)
class Period:
    start: date
    end: date  # included

    @classmethod
    def for_month(cls, year, month):
        return cls(date(year, month, 1), _last_day(year, month))

    @property
    def is_month(self):
        return (
            self.start.day == 1
            and (self.start.year, self.start.month) == (self.end.year, self.end.month)
            and self.end == _last_day(self.end.year, self.end.month)
        )

    @property
    def month(self):
        """(year, month) for a whole month, else None."""
        return (self.start.year, self.start.month) if self.is_month else None

    @property
    def days(self):
        return (self.end - self.start).days + 1

    def previous(self):
        """The month before, or the same number of days right before `start`."""
        if self.is_month:
            return Period.for_month(*shift(self.start.year, self.start.month, -1))
        end = self.start - timedelta(days=1)
        return Period(end - timedelta(days=self.days - 1), end)

    def query(self):
        if self.is_month:
            return {"month": month_param(*self.month)}
        return {"from": self.start.isoformat(), "to": self.end.isoformat()}

    @property
    def label(self):
        if self.is_month:
            return self.start.strftime("%B %Y")
        if self.start == self.end:
            return _day(self.start, year=True)
        if self.start.year != self.end.year:
            return f"{_day(self.start, year=True)} – {_day(self.end, year=True)}"
        return f"{_day(self.start)} – {_day(self.end, year=True)}"

    @property
    def slug(self):
        """For file names: 2026-11 or 2026-11-10_2026-11-24."""
        if self.is_month:
            return month_param(*self.month)
        return f"{self.start.isoformat()}_{self.end.isoformat()}"

    def prev_month(self):
        """The arrow target: the month before the start's month (design decision 5)."""
        return Period.for_month(*shift(self.start.year, self.start.month, -1))

    def next_month(self, today):
        """The month after the end's month, or None once it starts after today."""
        year, month = shift(self.end.year, self.end.month, 1)
        if date(year, month, 1) > today:
            return None
        return Period.for_month(year, month)


def _day(value, *, year=False):
    text = f"{value.day} {value.strftime('%b')}"
    return f"{text} {value.year}" if year else text


def _read_date(value):
    try:
        return date.fromisoformat((value or "").strip())
    except ValueError:
        return None


def parse_period(params, today):
    """The period from `from`/`to` (preferred) or `month`, with the spec's rules:
    no days after today, a reversed pair swapped, at most 92 days, and the
    current month when nothing can be read."""
    start, end = _read_date(params.get("from")), _read_date(params.get("to"))
    if start is None or end is None:
        return Period.for_month(*parse_month(params.get("month"), today))
    if start > end:
        start, end = end, start
    end = min(end, today)
    start = min(start, end)
    if (end - start).days + 1 > MAX_DAYS:
        end = start + timedelta(days=MAX_DAYS - 1)
    return Period(start, end)

