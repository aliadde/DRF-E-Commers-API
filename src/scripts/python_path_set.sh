#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

DJANGO_PROJECT_DIR="$(cd "$SCRIPT_DIR/../django_ecommers" && pwd)"

export PYTHONPATH="$DJANGO_PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}"

echo "PYTHONPATH=$PYTHONPATH"