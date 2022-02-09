#!/bin/sh
#   ! /usr/bin/env bash

# TODO: remove this!!!
# export PYTHONPATH=/app

# Let the DB start (justtest connection)
python ./app/backend_pre_start.py

# Run migrations
alembic upgrade head

# Create initial data in DB
python ./app/initial_data.py