FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install poetry==2.3.1
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction

COPY . .

RUN adduser \
    --disabled-password \
    --no-create-home \
    theatre_user

RUN chown -R theatre_user:theatre_user /app

USER theatre_user
