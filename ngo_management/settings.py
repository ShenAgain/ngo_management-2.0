"""
Django settings for ngo_management project.

Topic 4.4 – Database Configuration (SQLite)
Topic 6.2 – Session Management
Topic 6.3 – Password Hashing / Complexity
Topic 6.5 – Enterprise Auth Best Practices
"""

import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ────────────────────────────────────────────────────────────────
# Topic 7.1: OWASP Top 10 Protection
# Topic 7.2: Secure Authentication & Sessions

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-key")
DEBUG = os.environ.get("DEBUG", "1").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]

# Optional: base URL used when generating QR codes for scanning
# Example: http://192.168.1.6:8000
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "")

CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# Topic 7.1: Security Headers (OWASP Top 10)
SECURE_BROWSER_XSS_FILTER = True  # Enable browser XSS filter
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME type sniffing
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking
CSRF_COOKIE_SECURE = not DEBUG  # True in production (HTTPS only)
SESSION_COOKIE_SECURE = not DEBUG  # True in production (HTTPS only)
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

# Topic 7.2: Session Security
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access to CSRF cookie
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie

# ── Applications ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts.apps.AccountsConfig',
    'ngo',
    'registration',
    'notifications',
    # Django REST framework + filtering
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Topic 7.1 & 7.4: Security Middleware
    'ngo_management.middleware.SQLQueryMonitoringMiddleware',
    'ngo_management.middleware.RequestLoggingMiddleware',
    'ngo_management.middleware.RoleBasedAccessMiddleware',
]

ROOT_URLCONF = 'ngo_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ngo_management.wsgi.application'



DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ── Password validation (Topic 6.3 / 6.5) ───────────────────────────────────
# Django runs ALL validators in this list during password change/creation.
# Passwords are stored as PBKDF2-SHA256 hashes by default (never plain text).
AUTH_PASSWORD_VALIDATORS = [
    {   # Rejects passwords similar to username/email
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {   # Minimum 8 characters
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {   # Rejects common passwords (django's built-in list of ~20 000)
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {   # Rejects fully numeric passwords
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {   # Custom complexity: uppercase + lowercase + digit + special char
        'NAME': 'accounts.validators.PasswordComplexityValidator',
    },
]


# ── Session management (Topic 6.2) ──────────────────────────────────────────
# Sessions are stored in the database (django_session table).
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# Session expires after 8 hours of inactivity (enterprise working-day policy)
SESSION_COOKIE_AGE = 8 * 60 * 60        # 8 hours in seconds
# Session is destroyed when the browser is closed (belt-and-suspenders)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# Topic 6.5: only send session cookie over HTTPS in production
# NOTE: must not be hard-coded to False in production (Topic 7.2 / 9.1).
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True           # JS cannot read the cookie
CSRF_COOKIE_HTTPONLY = True

# Topic 9.1 – Session/cookie hardening (safe defaults for enterprise)
# Rotate session key on login (prevents session fixation)
SESSION_SAVE_EVERY_REQUEST = True


# ── Internationalisation ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kuala_Lumpur'
USE_I18N = True
USE_TZ = True

# ── Static files ─────────────────────────────────────────────────────────────
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ── Custom user model ─────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.CustomUser'

# ── Auth redirects ───────────────────────────────────────────────────────────
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/ngo/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ── Logging (request tracing via middleware) ─────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'ngo_management.middleware': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# -----------------------------
# Django REST Framework config
# -----------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
}

# -----------------------------
# Topic 9.2 – Caching (Redis)
# -----------------------------
# Falls back to local memory if REDIS_URL is not configured.
REDIS_URL = os.environ.get('REDIS_URL', '')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
            'TIMEOUT': 60,  # default TTL; override per-key as needed
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'ngo-management-locmem',
            'TIMEOUT': 60,
        }
    }

# -----------------------------
# Topic 10 – Async processing (Celery + Redis)
# -----------------------------
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', REDIS_URL or 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', '').lower() in ('1', 'true', 'yes')

# Run reminder job periodically (Topic 10.2)
CELERY_BEAT_SCHEDULE = {
    'send-activity-reminders-every-15-mins': {
        'task': 'notifications.tasks.send_upcoming_activity_reminders',
        'schedule': 15 * 60,
    },
}

# Email (demo-safe defaults)
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@ngo-portal.local')