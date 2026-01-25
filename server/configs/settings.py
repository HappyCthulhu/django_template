import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool((debug_value := os.environ.get("DEBUG")) and debug_value.lower() == "true")

# Application definition

LIBS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "drf_spectacular",
    "corsheaders",

    "pghistory",
    "pgtrigger",

    "multiselectfield",
]

_apps_subdir = "server.apps"

PROJECT_APPS = [
    f"{_apps_subdir}.core.apps.CoreConfig",
]

INSTALLED_APPS = LIBS + PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # Должно стоять как можно выше
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "server.configs.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "server.configs.wsgi.application"
X_FRAME_OPTIONS = "DENY"

# указываются только домены
ALLOWED_HOSTS: list[str] = os.environ["ALLOWED_HOSTS"].split(",")

# указываются с https:// с .com
CSRF_TRUSTED_ORIGINS: list[str] = os.environ["CSRF_TRUSTED_ORIGINS"].split(",")


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PORT": os.environ["POSTGRES_PORT"],
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Swagger settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Mines Highland API",
    "DESCRIPTION": "Project, thats allows you manage mines and licenses",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": True,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    },
    # Fixes file fields in Swagger UI
    "COMPONENT_SPLIT_REQUEST": True,
    "AUTHENTICATION_WHITELIST": [],
    "SERVE_AUTHENTICATION": [],
    "SECURITY_SCHEMES": {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
    },
    "SECURITY": [
        {
            "BearerAuth": [],
        },
    ],
}

# DRF settings
REST_FRAMEWORK = {
    "NON_FIELD_ERRORS_KEY": "error",
    # "EXCEPTION_HANDLER": "config.exceptions.drf_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": ("server.apps.core.auth.authentication.JWTAuthentication",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "Europe/Moscow"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

STATICFILES_DIRS = [BASE_DIR / "static"]  # здесь лежат исходники статики (например, пользовательская)

STATIC_ROOT = BASE_DIR / "www" / "public" / "static"  # здесь лежит финальная статика, которая будет доступна по url

# Media files
MEDIA_URL = "/media/"
# В production media хранится в named Docker volume и монтируется в Django-контейнер как /app/media
MEDIA_ROOT = Path("/app/media")

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth settings
AUTH_USER_MODEL = "core.User"


# JWT settings
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_ACCESS_LIFETIME = timedelta(minutes=15)
JWT_REFRESH_LIFETIME = timedelta(days=30)
JWT_ISSUER = os.environ.get("JWT_ISSUER") or None
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE") or None
