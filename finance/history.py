"""Daily wallet balances for the Wallets page trend line (wallets spec, "30-day balance trend").

Design decision 2 (redesign-wallets-page): start from the current balances and
walk backwards through the movements of the window, so the cost is two queries
no matter how many wallets or days.
"""

from collections import defaultdict
from datetime import timedelta

from django.db.models import Q

from .models import Category, Transaction, Transfer


def balance_history(wallets, today, days=30):
    """{wallet_id: [balance at the end of each day]}, oldest first, ending today.

    `wallets` must be annotated with `balance` (WalletQuerySet.with_balance()).
    """
    wallets = list(wallets)
    if not wallets:
        return {}
    ids = [w.pk for w in wallets]
    first = today - timedelta(days=days - 1)

    # movement[wallet][date] = net change on that day
    movement = defaultdict(lambda: defaultdict(int))
    for wallet_id, day, kind, amount in (
        Transaction.objects.filter(wallet_id__in=ids, date__gte=first, date__lte=today)
        .values_list("wallet_id", "date", "kind", "amount")
    ):
        movement[wallet_id][day] += amount if kind == Category.Kind.INCOME else -amount
    for source, target, day, amount in (
        Transfer.objects.filter(Q(from_wallet_id__in=ids) | Q(to_wallet_id__in=ids), date__gte=first, date__lte=today)
        .values_list("from_wallet_id", "to_wallet_id", "date", "amount")
    ):
        movement[source][day] -= amount
        movement[target][day] += amount

    history = {}
    for wallet in wallets:
        balance = wallet.balance
        points = []
        for offset in range(days):
            day = today - timedelta(days=offset)
            points.append(balance)
            balance -= movement[wallet.pk][day]
        history[wallet.pk] = points[::-1]
    return history
