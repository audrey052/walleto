# Walleto

Walleto is a personal finance web app for everyday life in Indonesia. You record income and spending across your wallets, set a budget per category, save toward goals, and ask an AI assistant about your own money.

The assistant answers only from your data. The model picks which tool to use and code computes every number, so the figures always match the rest of the app. Anything that changes your data, such as recording a transaction or applying a budget plan, waits for you to confirm it.

## Features

- **Home:** what is left of this month's budget, income and expenses compared with last month, daily spending, and spending by category.
- **Transactions:** income and expenses grouped by day, with filters and CSV export.
- **Wallets:** cash, bank and e-wallet balances, and transfers between them.
- **Budget:** a limit per category per month, with warnings as you get close.
- **Savings goals:** targets with deadlines and deposits from your wallets.
- **Assistant:** ask about your spending, record transactions in plain words, plan the rest of the month, and download a monthly PDF report.
- **Demo account:** three months of sample data, one click from the sign-in page.

## Tech stack

Django 5.2, Tailwind CSS v4, HTMX and Alpine.js, the OpenAI API with tool calling, xhtml2pdf, SQLite locally and PostgreSQL in production.

## Running locally

You need Python 3.11 and Node.js 20 or newer. Node is only used to build the stylesheet.

```bash
# 1. Python environment
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Settings: copy the example, then set SECRET_KEY (any long random string) and DEBUG=True
cp .env.example .env                 # Windows: copy .env.example .env

# 3. Database
python manage.py migrate

# 4. Stylesheet (or keep `npm run css:watch` running while you edit)
npm install
npm run css:build

# 5. Run
python manage.py runserver
```

Open http://127.0.0.1:8000, then create an account or choose **Try demo account**.

- **Assistant:** set `OPENAI_API_KEY` and `OPENAI_MODEL` in `.env` to use it. Without them the Assistant page says it is not set up, and the rest of the app works normally.
- **Demo data:** `python manage.py seed_demo` creates or resets the demo account. Other users are not touched.
- **Tests:** `python manage.py test` runs the test suite. It needs no API key.

## Deploying

Walleto is ready for a standard Django host:
- `build.sh` installs the packages, builds the stylesheet, collects the static files and migrates;
- `gunicorn config.wsgi` serves the app;
- `/healthz` answers health checks.

In production, set `DEBUG=False`, `SECRET_KEY`, `DATABASE_URL` (PostgreSQL) and the OpenAI values. See `.env.example` for every setting.
