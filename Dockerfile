# syntax=docker/dockerfile:1.7

# =============================================================
# Stage 1 — builder : install deps into a venv we copy later
# =============================================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System build deps (only needed at install time)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps into a venv we can copy to the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt


# =============================================================
# Stage 2 — runtime : slim image with the venv + the app
# =============================================================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=minivers.settings

# Runtime libs only: libpq for psycopg, gettext for Django i18n tooling,
# dumb-init to forward signals to the Django process.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libpq5 \
        gettext \
        dumb-init \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --shell /bin/bash --uid 1000 app

WORKDIR /app

# Copy the venv from the builder
COPY --from=builder /opt/venv /opt/venv

# The entrypoint lives OUTSIDE /app on purpose: docker-compose bind-mounts the
# host directory over /app at runtime, which would shadow the copy baked into
# the image (and with it, its executable bit).
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy the project. .dockerignore keeps junk out of the build context.
COPY --chown=app:app . /app

USER app

EXPOSE 8000

# Invoked through `bash` rather than executed directly, so the script only ever
# needs read permission — the host's exec bit becomes irrelevant.
ENTRYPOINT ["dumb-init", "--", "bash", "/usr/local/bin/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
