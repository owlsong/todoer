#!/bin/sh

export PYTHONPATH=/app
alembic revision --autogenerate -m "init user task"

