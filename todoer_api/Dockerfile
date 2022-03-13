FROM python:3.9-alpine as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app/

FROM base as builder

ARG poetry_build_arg

# add poetry
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apk add --no-cache rust cargo gcc libffi-dev musl-dev postgresql-dev openssl-dev
RUN pip install -U setuptools pip
RUN pip install -U poetry

# create virtual python env
RUN python -m venv /venv

# add fast api non-python dependencies
RUN apk add --no-cache --virtual .build-deps gcc libc-dev make 

# install poetry dependancies
COPY pyproject.toml poetry.lock ./
# here we can add --dev to include development 
RUN poetry export ${poetry_build_arg} -f requirements.txt | /venv/bin/pip install -r /dev/stdin

# copy files to container - recursive
COPY . /app

RUN poetry build && /venv/bin/pip install dist/*.whl

FROM base as final
RUN apk add --no-cache libffi libpq
COPY --from=builder /venv /venv
COPY . /app

# move script files to root dir
RUN mv /app/start.sh /
RUN chmod +x /start.sh

RUN mv /app/start-reload.sh /
RUN chmod +x /start-reload.sh

RUN mv /app/gunicorn_conf.py /

# ENV PYTHONPATH=/app
ENV PYTHONPATH=/venv \
    PATH=/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin 

# EXPOSE 80

# Run the start script, it will check for an /app/prestart.sh script (e.g. for migrations)
# And then will start Gunicorn with Uvicorn
# CMD ["/start.sh"]
CMD ["/start-reload.sh"]

