"""The six main sections of Walleto, in sidebar order.

Titles and subtitles follow docs/STYLE.md section 6.
"""

SECTIONS = [
    {
        "key": "dashboard",
        "short": "Home",
        "title": "Dashboard",
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
        "url_name": "core:transactions",
    },
    {
        "key": "wallets",
        "short": "Wallets",
        "title": "Wallets",
        "subtitle": "Balances across your cash, bank and e-wallets.",
        "icon": "wallet",
        "url_name": "core:wallets",
    },
    {
        "key": "budget",
        "short": "Budget",
        "title": "Budget",
        "subtitle": "Monthly limits per category.",
        "icon": "budget",
        "url_name": "core:budget",
    },
    {
        "key": "savings",
        "short": "Goals",
        "title": "Savings goals",
        "subtitle": "Track progress toward what you're saving for.",
        "icon": "goal",
        "url_name": "core:savings",
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
