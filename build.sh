#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Automatically create a superuser if environment variables are provided
if [[ -n "${DJANGO_SUPERUSER_USERNAME}" && -n "${DJANGO_SUPERUSER_PASSWORD}" ]]; then
  echo "Creating superuser..."
  python manage.py createsuperuser --noinput || echo "Superuser already exists."
fi
