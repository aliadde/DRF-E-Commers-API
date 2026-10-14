#!/usr/bin/env bash

echo "--> docker compose up -d"
docker compose up -d

echo "--> docker exec -it django-ecommers-api-1 uv run pytest"
docker exec -it django-ecommers-api-1 uv run pytest

echo "--> docker compose down -v"
docker compose down -v
