### django_template

Personal template for quickly bootstrapping a **Django REST API** project: Postgres, JWT authentication, Swagger/OpenAPI, basic system checks, Docker environment, and a minimal set of dev commands.

### Project initialization (after using the template)

After creating a new repository from this template, rename the Django project package and internal imports:

Run this **immediately after creating the repository from the template**:

- **BEFORE installing dependencies**
- **BEFORE running migrations**
- **BEFORE starting Docker or `runserver`**

```bash
./scripts/rename_project.sh <project_name>
```

Important:

- Run it **only once** (the script creates `.project_renamed` and refuses to run again).
- It renames `server/` → `<project_name>/` and updates internal imports and `DJANGO_SETTINGS_MODULE`.
- `<project_name>` must be a valid Python package name in **snake_case**:
  - valid: `my_project`
  - invalid: `my-project`, `MyProject`

### Development setup

- pre-commit is **optional**, but **strongly recommended**
- Install pre-commit: `pip install pre-commit`
- Install hooks: `pre-commit install` (hooks will run automatically on `git commit`)

### What it’s for

- **Create a new backend project fast** without starting from a blank slate.
- **A consistent starter stack** (DRF + JWT + Postgres + Swagger) and conventions.
- **Production-ready baseline**: Gunicorn, migrations/static in the entrypoint.

### What’s included out of the box

- **API**
  - Healthcheck: `GET /api/core/health/` → `{"status":"ok"}`
  - Swagger/OpenAPI:
    - `GET /api/schema/` (OpenAPI schema)
    - `GET /api/swagger/` (Swagger UI)
- **JWT auth (stateless)**
  - `POST /api/auth/login/` — issues `access/refresh`
  - `POST /api/auth/refresh/` — refreshes `access` using `refresh`
  - `POST /api/auth/logout/` — 204 (API symmetry; tokens are not stored server-side)
  - DRF authentication: `Authorization: Bearer <access>`
- **Custom user model**
  - `AUTH_USER_MODEL = core.User`
  - Login by `email`
- **PostgreSQL**
  - Supports running via `docker compose`
  - `psycopg2-binary`
- **Model change audit (pghistory)**
  - `@track_history` decorator for models
  - Django system check: warns if a model doesn’t have a pghistory Event model
  - Command to auto-add `@track_history`: `./manage.py add_pg_history_model`
- **CORS**
  - `django-cors-headers`
- **Dev/quality**
  - `ruff` (lint/format), `mypy` + `django-stubs`, `djangorestframework-stubs`
- **HTTP provider for external requests**
  - `server/apps/core/provider.py`: `BaseProvider` based on `requests` with retry/backoff (urllib3 Retry)
  - Response normalization: `NormalizedResponse(status_code, headers, body)`
  - Unified error type: `ProviderRequestError` (url/status_code/response_body/original_exception)

### Main dependencies

See `pyproject.toml`, key ones:

- **Django** `>=5.2`
- **Django REST Framework**
- **drf-spectacular** (OpenAPI/Swagger)
- **PyJWT[crypto]** (JWT)
- **Postgres**: `psycopg2-binary`
- **django-cors-headers**
- **django-pghistory**
- **loguru**
- **gunicorn** (enabled in the Docker image by default)

### Quick start (Docker)

1) Create `.env` in the project root (docker-compose reads environment variables from the shell/`.env`):

```env
# Django
DJANGO_SETTINGS_MODULE=server.configs.settings
DJANGO_SECRET_KEY=change-me
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Postgres
POSTGRES_DB=template
POSTGRES_USER=template
POSTGRES_PASSWORD=template
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

# Optional JWT
# JWT_SECRET_KEY=change-me-too
# JWT_ISSUER=
# JWT_AUDIENCE=

# Optional admin auto-provision (used by docker-entrypoint.sh)
# WARNING: the current `core.User` model requires `first_name/last_name`, so
# auto-creating a superuser will work only if you adapt the model/manager
# (or add default values). It’s safer to keep this disabled by default.
# ADMIN_LOGIN=admin
# ADMIN_EMAIL=admin@example.com
# ADMIN_PASSWORD=admin
```

2) Bring everything up:

```bash
docker compose up --build
```

3) Check:

- **Health**: `GET /api/core/health/`
- **Swagger**: `GET /api/swagger/`
- **Admin**: `GET /api/admin/`

Note: `docker-entrypoint.sh` contains logic to auto-create a superuser via `ADMIN_*`, but with the current template state it’s safer to keep it disabled (see the comment in the `.env` example). You can create an admin user manually:

```bash
docker compose exec django /app/.venv/bin/python manage.py createsuperuser
```

### Local run (without Docker for Django, but with Postgres in Docker)

Requirements: Python **>= 3.12**, `uv` installed.

1) Install dependencies:

```bash
pip install uv
uv sync --frozen
```

2) Start Postgres:

```bash
docker compose up -d postgres
```

3) Export env vars (see the `.env` block above) and run:

```bash
./manage.py migrate
./manage.py runserver
```

### Justfile (common commands)

If you use `just`, the repo includes aliases:

- **`just run`**: start Postgres and run `runserver`
- **`just up [args]`**: `docker compose up ...`
- **`just down`**: `docker compose down`
- **`just migrate [args]`**, **`just makemigrations [args]`**, **`just mmm`**
- **`just add_pg_history_model [args]`**: auto-add `@track_history` to models
- **`just dump`**: pg_dump to a file (requires `POSTGRES_*` + `DUMPS_DIR`)

### Auth endpoints (example)

- **Login**: `POST /api/auth/login/`

```json
{ "email": "admin@example.com", "password": "admin" }
```

Response:

```json
{
  "access": "<jwt>",
  "refresh": "<jwt>",
  "user": { "id": 1, "email": "admin@example.com", "first_name": "Admin", "last_name": "User" }
}
```

- **Refresh**: `POST /api/auth/refresh/`

```json
{ "refresh": "<jwt>" }
```

Response:

```json
{ "access": "<jwt>" }
```

### Project structure

- `server/configs/` — Django settings/urls/asgi/wsgi
- `server/apps/core/` — core app:
  - `auth/` — JWT auth (login/refresh/logout, authentication backend)
  - `models/` — `User` and base models
  - `views/health.py` — healthcheck
  - `history.py` — `@track_history`
  - `provider.py` — base HTTP client for external integrations (retry + normalization)
  - `checks.py` — system checks (pghistory + optional access-policy)

### Configuration notes

- **`ALLOWED_HOSTS`**: comma-separated list of domains (without scheme).
- **`CSRF_TRUSTED_ORIGINS`**: comma-separated list of origins (with scheme, e.g. `https://example.com`).
- **`DEBUG`**: enabled only if the variable equals `"true"` (case-insensitive).
