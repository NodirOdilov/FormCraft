"""
Development-specific Django settings.
"""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Use console email backend in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relax throttling for development
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/hour",
    "user": "10000/hour",
}

# Disable WhiteNoise manifest in dev to avoid missing file errors
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# CORS allow all in development
CORS_ALLOW_ALL_ORIGINS = True
