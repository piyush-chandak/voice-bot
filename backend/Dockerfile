FROM python:3.12-slim as builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR $PYSETUP_PATH
COPY pyproject.toml ./
RUN poetry install --only main --no-root

FROM python:3.12-slim as development
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/pysetup/.venv/bin:$PATH"
WORKDIR /workspace
COPY --from=builder /opt/pysetup /opt/pysetup

RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq-dev git \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM python:3.12-slim as production
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/pysetup/.venv/bin:$PATH"
WORKDIR /app
COPY --from=builder /opt/pysetup /opt/pysetup
RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY . /app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
