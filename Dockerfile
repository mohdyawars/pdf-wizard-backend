# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
  gcc \
  build-essential \
  libgl1-mesa-glx \
  libglib2.0-0 \
  tesseract-ocr \
  && rm -rf /var/lib/apt/lists/*

ARG UID=10001
RUN adduser \
  --disabled-password \
  --gecos "" \
  --home "/nonexistent" \
  --shell "/sbin/nologin" \
  --no-create-home \
  --uid "${UID}" \
  appuser

RUN --mount=type=cache,target=/root/.cache/pip \
  --mount=type=bind,source=requirements.txt,target=requirements.txt \
  python -m pip install -r requirements.txt

USER appuser

COPY . .

EXPOSE 8000

CMD python manage.py runserver 0.0.0.0:8000
