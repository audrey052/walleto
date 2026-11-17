"""`?month=YYYY-MM` handling shared by the Transactions and Budget pages."""


def shift(year, month, delta):
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def parse_month(value, today, *, allow_next=False):
    """`YYYY-MM` -> (year, month).

    Invalid values, and months after the current one, fall back to the current
    month. With `allow_next`, the month right after the current one is allowed
    too (Budget, so a plan can be made before the month starts).
    """
    current = (today.year, today.month)
    try:
        year, month = (int(part) for part in (value or "").split("-"))
        if not 1 <= month <= 12 or year < 2000:
            raise ValueError
    except ValueError:
        return current
    latest = shift(*current, 1) if allow_next else current
    if (year, month) > latest:
        return current
    return year, month


def month_param(year, month):
    return f"{year:04d}-{month:02d}"
