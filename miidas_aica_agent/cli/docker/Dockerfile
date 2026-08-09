ARG PYTHON_VERSION=3.14
ARG DEBIAN_VERSION=trixie
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_VERSION}

ENV APP_HOME=/home/app/batch
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system app && adduser --system --group app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential libpq-dev curl git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements-dev.txt .
RUN pip install --upgrade "pip>=25,<27" && pip --version
RUN pip install -r requirements-dev.txt

RUN chown -R app:app $APP_HOME

USER app
