#!/usr/bin/env bash

set -e

fastapi run app/main.py --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" --workers "${WORKERS:-4}"
