import os

from .base import *  # noqa

# check for secret key
if os.environ.get("BARYON_SECRET_KEY") is None:
    raise Exception(
        "Please set the env variable `BARYON_SECRET_KEY` when running in production"
    )

DEBUG = False

ALLOWED_HOSTS = [
    "baryon.supercollider.online",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": os.environ.get("POSTGRES_PORT"),
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
    }
}

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5

# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("""{{cookiecutter.author_name}}""", "{{cookiecutter.email}}")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = "Baryon <noreply@baryon.supercollider.online>"
