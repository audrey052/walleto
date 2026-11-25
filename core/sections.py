"""The six main sections of Walleto, in sidebar order.

Titles and subtitles are short and plain: no taglines (app-shell spec).
"""

SECTIONS = [
    {
        "key": "dashboard",
        "short": "Home",
        "title": "Home",  # same as the phone bar's short label
        "subtitle": "Your money this month at a glance.",
        "icon": "dashboard",
        "url_name": "core:dashboard",
    },
    {
        "key": "transactions",
        "short": "Activity",
        "title": "Transactions",
        "subtitle": "Every income and expense, by date.",
        "icon": "transactions",
        "url_name": "finance:transactions",
        "match": ("finance:transaction", "finance:transfer"),
    },
    {
        "key": "wallets",
        "short": "Wallets",
        "title": "Wallets",
        "subtitle": "Balances across your cash, bank and e-wallets.",
        "icon": "wallet",
        "url_name": "finance:wallets",
        # Every view whose name starts with this is part of the section (list, create, edit...).
        "match": "finance:wallet",
    },
    {
        "key": "budget",
        "short": "Budget",
        "title": "Budget",
        "subtitle": "Monthly limits per category.",
        "icon": "budget",
        "url_name": "finance:budget",
        "match": "finance:budget",
    },
    {
        "key": "savings",
        "short": "Goals",
        "title": "Savings goals",
        "subtitle": "Track progress toward what you're saving for.",
        "icon": "goal",
        "url_name": "finance:goals",
        # Every goal view: list, detail, create, edit, deposit, withdraw, delete (add-savings-goals).
        "match": "finance:goal",
    },
    {
        "key": "assistant",
        "short": "Assistant",
        "title": "Assistant",
        "subtitle": "Ask about your spending, or plan the rest of the month.",
        "icon": "assistant",
        "url_name": "core:assistant",
    },
]

SECTIONS_BY_KEY = {section["key"]: section for section in SECTIONS}
