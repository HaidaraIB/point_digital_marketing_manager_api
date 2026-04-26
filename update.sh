#!/usr/bin/env bash
# Pull latest from GitHub and redeploy the Django API (see DEPLOY.md §12).
# Run on the VPS from the repo root, or from anywhere: ./update.sh
# Typical path: /var/www/point_digital_marketing_manager_api/update.sh

echo "[update] pip install -r requirements.txt"
pip install -r requirements.txt

echo "[update] makemigrations"
python manage.py makemigrations

echo "[update] migrate"
python manage.py migrate

echo "[update] collectstatic"
python manage.py collectstatic --noinput

echo "[update] restart Gunicorn (systemd)"
sudo systemctl restart point_digital_marketing_manager_api

echo "[update] Done."
