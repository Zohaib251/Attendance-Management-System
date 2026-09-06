#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Run Alembic migrations if configured
# alembic upgrade head
