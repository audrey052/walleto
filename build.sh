#!/usr/bin/env bash
# Render build (polish-and-deploy design decision 4). Runs before the new version takes traffic;
# any failing step fails the deploy and the previous version keeps serving.
set -o errexit
set -o nounset
set -o pipefail

python -m pip install --upgrade pip
pip install -r requirements.txt

# static/css/ is not in git: build the stylesheet from static/src/app.css.
npm ci
npm run css:build

python manage.py collectstatic --no-input
python manage.py migrate --no-input
