"""Demo account data (demo-account spec, design.md decision 9).

`build_demo(today)` replaces the demo user's wallets, transactions and transfers
with three months of realistic data ending `today`. It is deterministic for a
given date and never lets a wallet go below zero.
"""

import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction

from .models import Category, Transaction, Transfer, Wallet

DEMO_EMAIL = "demo@walleto.app"
DEMO_NAME = "Aditya Ramadhan"

# name, type, starting balance (in creation order, which sets the monogram colors)
WALLETS = [
    ("BCA", Wallet.Type.BANK, 4_250_000),
    ("GoPay", Wallet.Type.EWALLET, 85_000),
    ("OVO", Wallet.Type.EWALLET, 42_500),
    ("Bank Jago", Wallet.Type.BANK, 1_500_000),
    ("Cash", Wallet.Type.CASH, 350_000),
]

# description, notes, category, wallet, min, max, chance per day
EVERYDAY = [
    ("GoFood", ["Lunch delivery", "Dinner for two", "Team lunch order"], "Food & drinks", "GoPay", 35_000, 120_000, 0.45),
    ("Kopi Kenangan", ["An afternoon pick-me-up", "Coffee and a sandwich"], "Food & drinks", "GoPay", 18_000, 48_000, 0.35),
    ("Fore Coffee", ["Coffee and pastries"], "Food & drinks", "OVO", 28_000, 62_000, 0.12),
    ("Warung Bu Kris", ["Lunch break"], "Food & drinks", "Cash", 18_000, 42_000, 0.35),
    ("Bakmi GM", ["Dinner on the way home", "Lunch with colleagues"], "Food & drinks", "BCA", 45_000, 115_000, 0.10),
    ("Grab", ["Ride to the office", "Ride home"], "Transport", "OVO", 18_000, 65_000, 0.30),
    ("Gojek", ["Quick ride", "Ride to the station"], "Transport", "GoPay", 14_000, 42_000, 0.30),
    ("Indomaret", ["Snacks and water", "Weekly essentials"], "Shopping", "Cash", 22_000, 160_000, 0.20),
    ("Tokopedia", ["Home supplies", "Desk essentials"], "Shopping", "BCA", 79_000, 420_000, 0.05),
    ("Shopee", ["Personal care", "Phone case"], "Shopping", "OVO", 45_000, 230_000, 0.05),
    ("Cinema XXI", ["Movie night"], "Entertainment", "OVO", 50_000, 125_000, 0.04),
    ("Kimia Farma", ["Vitamins", "Cold medicine"], "Health", "BCA", 35_000, 155_000, 0.03),
]

# description, note, category, wallet, day of month, min, max
MONTHLY = [
    ("Monthly salary", "Salary", "Salary", "BCA", 1, 12_500_000, 12_500_000),
    ("IndiHome", "Monthly internet", "Bills & utilities", "BCA", 3, 329_000, 329_000),
    ("Spotify", "Monthly subscription", "Entertainment", "BCA", 4, 54_990, 54_990),
    ("Telkomsel", "Mobile plan", "Bills & utilities", "BCA", 5, 150_000, 165_000),
    ("PAM Jaya", "Water bill", "Bills & utilities", "BCA", 9, 128_000, 176_000),
    ("PLN", "Electricity token", "Bills & utilities", "BCA", 12, 203_000, 253_000),
    ("Freelance design", "Logo project", "Other income", "Bank Jago", 18, 1_250_000, 2_250_000),
]

# description, note, category, wallet, weekday (Monday = 0), min, max
WEEKLY = [
    ("Superindo", "Weekly groceries", "Shopping", "BCA", 5, 135_000, 365_000),
    ("Pertamina", "Fuel refill", "Transport", "BCA", 6, 150_000, 240_000),
    ("LaundryKlin", "Weekly laundry", "Others", "Cash", 2, 35_000, 62_000),
]

TRANSFERS = [
    # rule ("monthly": day of month, "weekly": weekday), from, to, amount, note
    ("monthly", 2, "BCA", "Bank Jago", 2_000_000, "Monthly savings"),
    ("monthly", 1, "BCA", "Cash", 500_000, "Cash withdrawal"),
    ("monthly", 15, "BCA", "Cash", 500_000, "Cash withdrawal"),
    ("weekly", 0, "BCA", "GoPay", 400_000, "Top up for the week"),
    ("weekly", 3, "BCA", "OVO", 250_000, "Top up"),
]


def _first_of_month(day, months_back):
    index = day.year * 12 + (day.month - 1) - months_back
    return date(index // 12, index % 12 + 1, 1)


def _amount(rng, low, high):
    """Irregular, realistic amounts: multiples of 500, rarely round thousands."""
    if low == high:
        return low
    return max(500, round(rng.randint(low, high) / 500) * 500)


def get_demo_user():
    User = get_user_model()
    user, created = User.objects.get_or_create(
        email=DEMO_EMAIL, defaults={"full_name": DEMO_NAME}
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


@db_transaction.atomic
def build_demo(today):
    user = get_demo_user()
    # Children first: wallets are PROTECTed by transactions and transfers.
    Transaction.objects.filter(user=user).delete()
    Transfer.objects.filter(user=user).delete()
    Wallet.objects.filter(user=user).delete()
    Category.objects.filter(user=user).delete()

    rng = random.Random(f"walleto-demo-{today.isoformat()}")
    categories = {c.name: c for c in Category.objects.for_user(user)}
    wallets = {}
    balances = {}
    for name, kind, start in WALLETS:
        wallets[name] = Wallet.objects.create(user=user, name=name, type=kind, initial_balance=start)
        balances[name] = start

    transactions, transfers = [], []

    def spend(day, description, note, category, wallet, amount):
        if categories[category].kind == Category.Kind.EXPENSE:
            if balances[wallet] < amount:
                return  # never overdraw a demo wallet
            balances[wallet] -= amount
        else:
            balances[wallet] += amount
        transactions.append(Transaction(
            user=user, wallet=wallets[wallet], category=categories[category],
            kind=categories[category].kind, amount=amount, date=day,
            description=description, note=note,
        ))

    def move(day, source, target, amount, note):
        if balances[source] < amount:
            return
        balances[source] -= amount
        balances[target] += amount
        transfers.append(Transfer(
            user=user, from_wallet=wallets[source], to_wallet=wallets[target],
            amount=amount, date=day, note=note,
        ))

    day = _first_of_month(today, 2)
    while day <= today:
        # Income and bills first, then money moves, then everyday spending.
        for description, note, category, wallet, dom, low, high in MONTHLY:
            if day.day == dom:
                spend(day, description, note, category, wallet, _amount(rng, low, high))
        for rule, when, source, target, amount, note in TRANSFERS:
            if (rule == "monthly" and day.day == when) or (rule == "weekly" and day.weekday() == when):
                move(day, source, target, amount, note)
        for description, note, category, wallet, weekday, low, high in WEEKLY:
            if day.weekday() == weekday:
                spend(day, description, note, category, wallet, _amount(rng, low, high))
        for description, notes, category, wallet, low, high, chance in EVERYDAY:
            if rng.random() < chance:
                spend(day, description, rng.choice(notes), category, wallet, _amount(rng, low, high))
        day += timedelta(days=1)

    # bulk_create skips save(), so kind was set explicitly above.
    Transaction.objects.bulk_create(transactions)
    Transfer.objects.bulk_create(transfers)
    return user
