# Deploying Walleto

This guide puts Walleto online with two free services:

- **[Neon](https://neon.tech):** the PostgreSQL database.
- **[Render](https://render.com):** the web app. It builds the code from GitHub and runs it with gunicorn.

Everything is set up by hand in their dashboards. It takes about 20 minutes the first time.

```
GitHub repo ──push──▶ Render web service (Singapore) ──SSL──▶ Neon PostgreSQL (Singapore)
                       build.sh, then gunicorn                 DATABASE_URL
```

## Before you start

- The code is pushed to a GitHub repository you can connect to Render.
- You have an OpenAI API key, the model name, and the reasoning setting you use locally (`OPENAI_MODEL`, `OPENAI_REASONING_EFFORT` in your `.env`).
- Locally, `python manage.py test` passes.

## 1. Create the database on Neon

1. Sign up at neon.tech (GitHub sign-in is fine) and create a project:
   - **Project name:** `walleto`
   - **Postgres version:** the default
   - **Region:** AWS Asia Pacific (Singapore), `ap-southeast-1`. This keeps it next to the Render service.
2. On the project dashboard, choose **Connect**.
3. Turn **Connection pooling off**. You need the *direct* connection string, whose host does not contain `-pooler`.
4. Copy the connection string. It looks like this:

   ```
   postgresql://<user>:<password>@ep-<name>.ap-southeast-1.aws.neon.tech/<database>?sslmode=require
   ```

   Keep it private. It is the `DATABASE_URL` value in step 2, and it never goes into the repository.

Why not the pooled string: with 2 gunicorn workers, Walleto uses only a few connections. The pooler would also need extra Django settings.

## 2. Create the web service on Render

1. Sign up at render.com and connect your GitHub account.
2. Choose **New → Web Service**, and pick the Walleto repository.
3. Fill in the form:

   | Field | Value |
   |---|---|
   | Name | `walleto` (this becomes `walleto.onrender.com`, or a variant if the name is taken) |
   | Language | Python 3 |
   | Branch | `main` |
   | Region | Singapore |
   | Root directory | *(empty)* |
   | Build command | `./build.sh` |
   | Start command | `gunicorn config.wsgi --workers 2 --timeout 60 --access-logfile -` |
   | Instance type | Free |

4. Under **Environment variables**, add:

   | Key | Value | Where it comes from |
   |---|---|---|
   | `PYTHON_VERSION` | `3.11.9` | Same as `.python-version` |
   | `NODE_VERSION` | `22` | Needed to build the CSS |
   | `DEBUG` | `False` | |
   | `SECRET_KEY` | a long random string | Run `python -c "import secrets; print(secrets.token_urlsafe(50))"` and paste the output |
   | `DATABASE_URL` | the Neon connection string | Step 1 |
   | `OPENAI_API_KEY` | your key | platform.openai.com |
   | `OPENAI_MODEL` | for example `gpt-6-luna` | Your local `.env` |
   | `OPENAI_REASONING_EFFORT` | for example `none` | Your local `.env` |

   You don't need `ALLOWED_HOSTS` for the `.onrender.com` address, because Render provides `RENDER_EXTERNAL_HOSTNAME` and Walleto adds it automatically. Set `ALLOWED_HOSTS` only if you add a custom domain, for example `walleto.example.com`.

5. Under **Advanced**, set **Health Check Path** to `/healthz` and leave **Auto-Deploy** on.
6. Choose **Create Web Service**.

The first build takes a few minutes. `build.sh` does five things, and any failure stops the deploy:

1. installs the Python packages from `requirements.txt`;
2. installs the Node packages (`npm ci`);
3. builds the stylesheet (`npm run css:build`);
4. collects the static files (`collectstatic`);
5. creates the tables in Neon (`migrate`).

## 3. Check the first deploy

Open each of these on your `https://<name>.onrender.com` address:

- [ ] `/healthz` shows `ok`.
- [ ] `http://<name>.onrender.com/` (plain HTTP) redirects to `https://`.
- [ ] The sign-in page is styled, with the logo, the green button and the Nunito font.
- [ ] **Try demo account** opens Home with three months of data. The first click creates the demo data, so it is a little slower.
- [ ] Ask the Assistant one question, for example "How much did I spend this month?".
- [ ] `/no-such-page/` shows "Page not found".
- [ ] Put the live link in the README, in the "Live demo" line.

## Updating

- **Normal updates:** push to `main`. Render builds and deploys automatically, and the old version keeps serving until the new one passes `/healthz`.
- **New migrations** run during the build. If a migration fails, the deploy fails and nothing changes.
- **Rolling back:** in Render, open **Events**, pick an earlier successful deploy, and choose **Rollback**. If that deploy used an older migration, check that the code still works with the newer tables first.

## Refreshing the demo data

The demo data is created once, on the first "Try demo account". It is not reset automatically, so visitors' changes stay and the dates slowly age. To rebuild it for today, run this on your own machine, because Render's free plan has no shell:

```bash
# Git Bash / macOS / Linux
DATABASE_URL="<the Neon connection string>" python manage.py seed_demo
```

```powershell
# PowerShell
$env:DATABASE_URL = "<the Neon connection string>"; python manage.py seed_demo; Remove-Item Env:DATABASE_URL
```

This replaces only the demo user's data. Registered users are not touched.

## Free plan limits

- **Render free web service:** it sleeps after about 15 minutes without visits, and the next visit takes up to a minute to wake it. There is also a monthly limit on running hours. For a portfolio demo that is fine. Mention it if you share the link.
- **Neon free plan:** 0.5 GB of storage, which is plenty, and a monthly allowance of compute. The database suspends itself after about 5 minutes idle and wakes on the next query in about a second. Walleto checks its connection before using it, so this never shows an error.
- **OpenAI:** each signed-in user, the demo included, can ask 30 questions a day. The demo account is shared, so its 30 questions are shared by all visitors, which also caps the API cost.

Limits change; check the current numbers on each service's pricing page.

## Troubleshooting

| Problem | Cause and fix |
|---|---|
| Build fails at `npm ci` with "npm: command not found" | Node is missing. Check that `NODE_VERSION` is set, then choose **Manual Deploy → Clear build cache & deploy**. |
| Build fails at `migrate` with a connection error | `DATABASE_URL` is wrong or uses the pooled host. Copy the direct string from Neon again, including `?sslmode=require`. |
| Build fails with `Set SECRET_KEY in the environment` | `SECRET_KEY` is missing or empty. |
| "Bad Request (400)" on every page | The host name is not allowed. On `.onrender.com` this should not happen. With a custom domain, add it to `ALLOWED_HOSTS`. |
| "Too many redirects" | Something in front of Render (a proxy or CDN) strips `X-Forwarded-Proto`. Open the site directly on its `.onrender.com` address. |
| Pages load without styles | `collectstatic` did not run, or `DEBUG` is not `False`. Check the build log for `static files copied`. |
| The Assistant says it is not set up | `OPENAI_API_KEY` or `OPENAI_MODEL` is missing. Add it, then redeploy. |
| The first page after a quiet period is slow | Render is waking up, and possibly Neon too. This is expected on the free plans. |
