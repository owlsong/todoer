## Local Setup

* `pip install poetry`
* Install dependencies `cd` into the directory where the `pyproject.toml` is located then `poetry install`
* Run the FastAPI server via poetry `poetry run uvicorn main:app --reload`
* Open http://localhost:8001/

## docker-compose Setup

## Dockerfile
Production start script: start.sh
Development start script: start-reload.sh

## update database
On the todoer-api container open a shell:
        docker-compose exec todoer-api sh
[Note of crashing then insert tail -f /dev/null to pause script]

Then on the todoer-api container :
        alembic revision --autogenerate -m "<comment here>"

Then check for new files in (to check changesa are OK):
./todoer_api/alembic/versions/

## Run tests
do from cmd line:
        docker-compose exec todoer-api pytest