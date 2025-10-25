#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/opt/arb-bot"
SERVICE_NAME="arb-bot"

cd "$REPO_DIR"

echo "[deploy] pulling latest code"
git pull --ff-only

echo "[deploy] ensuring virtualenv is active"
source .venv/bin/activate

echo "[deploy] installing python dependencies"
pip install -r requirements.txt

echo "[deploy] running database migrations"
alembic upgrade head

echo "[deploy] reloading service"
sudo systemctl restart "${SERVICE_NAME}.service"

echo "[deploy] done"
