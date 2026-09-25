#!/bin/sh
set -e

uv run python src/manage.py migrate

uv run python src/manage.py createsuperuser --noinput || true

exec "$@"
