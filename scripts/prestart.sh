#!/usr/bin/env bash

set -e
set -x

# Apply migrations
alembic upgrade head

# Seed the first superuser from settings
python -c "from sqlmodel import Session; from app.core.db import engine, init_db; init_db(Session(engine))"
