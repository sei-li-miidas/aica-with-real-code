# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.14
ARG DEBIAN_VERSION=trixie
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV APP_HOME=/home/app/batch
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

RUN addgroup --system app && adduser --system --group app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY ./src $APP_HOME/src
COPY ./run.sh $APP_HOME/

RUN chown -R app:app $APP_HOME

USER app
