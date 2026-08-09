"""
Django settings for minivers project.

All deployment-tunable values are read from environment variables (see .env.example).
A SQLite fallback is used when no DB credentials are provided, so the project
still runs locally without any setup.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env (if present) into os.environ. No-op if the file is missing.
load_dotenv(BASE_DIR / ".env")


def env(key: str, default: str | None = None) -> str | None:
    """Read an environment variable, returning ``default`` when unset."""
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    """Parse a boolean environment variable (true/1/yes/on)."""
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_int(key: str, default: int) -> int:
    """Parse an integer environment variable, falling back to ``default`` on error."""
    raw = os.environ.get(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def env_path(key: str, default: Path) -> Path:
    """Resolve a path environment variable.

    Absolute values are used as-is; relative ones are anchored to ``BASE_DIR``.
    Absolute paths matter under Docker, where writable directories live outside
    the bind-mounted source tree.
    """
    raw = os.environ.get(key)
    if not raw:
        return default
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else BASE_DIR / candidate


# --- Core --------------------------------------------------------------------

SECRET_KEY = env("DJANGO_SECRET_KEY", "django-insecure-dev-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "*").split(",") if h.strip()]


# --- Applications ------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "main",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "minivers.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "minivers.wsgi.application"
ASGI_APPLICATION = "minivers.asgi.application"


# --- Database ----------------------------------------------------------------
#
# When DB_* variables are set (e.g. in docker-compose) we use PostgreSQL.
# Otherwise we fall back to SQLite so the project still runs with `manage.py
# runserver` on a fresh checkout, no env file needed.

_db_engine = env("DB_ENGINE", "sqlite")

if _db_engine == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", "minivers"),
            "USER": env("DB_USER", "minivers"),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "db"),
            "PORT": env("DB_PORT", "5432"),
            "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
        }
    }
elif _db_engine == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": env("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        }
    }
else:
    raise RuntimeError(
        f"Unknown DB_ENGINE: {_db_engine!r}. Expected 'postgres' or 'sqlite'."
    )


# --- I18N --------------------------------------------------------------------

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True


# --- Static / media ----------------------------------------------------------

STATIC_URL = env("STATIC_URL", "static/")
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = env_path("STATIC_ROOT", BASE_DIR / "staticfiles")

MEDIA_URL = env("MEDIA_URL", "media/")
MEDIA_ROOT = env_path("MEDIA_ROOT", BASE_DIR / "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
