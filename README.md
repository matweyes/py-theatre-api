# Theatre API

RESTful backend application for browsing theatrical performances, selecting available seats, and reserving tickets online.

Built with Django REST Framework, JWT authentication, PostgreSQL, and Docker.

## Current Status

**Phase 1 — Project Foundation** is complete:

- Django project scaffold (`theatre_service`)
- Custom email-based User model (no username)
- JWT authentication (register, login, refresh, verify, profile)
- PostgreSQL database configuration via environment variables
- API documentation with drf-spectacular (Swagger UI + ReDoc)
- Docker + Docker Compose setup
- `wait_for_db` management command
- Flake8 linting with plugins

## Tech Stack

- Python 3.12
- Django 6.0
- Django REST Framework 3.17
- Simple JWT (token authentication)
- drf-spectacular (OpenAPI / Swagger)
- PostgreSQL 16
- Docker & Docker Compose
- Poetry (dependency management)

## Project Structure

```
py-theatre-api/
├── theatre_service/           # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── user/                      # Custom user app
│   ├── models.py              # User + UserManager (email-based)
│   ├── serializers.py         # UserSerializer
│   ├── views.py               # Register + profile views
│   ├── urls.py                # Auth endpoints
│   ├── admin.py               # Custom UserAdmin
│   └── management/
│       └── commands/
│           └── wait_for_db.py
├── Dockerfile
├── docker-compose.yaml
├── pyproject.toml
├── poetry.lock
├── .env.sample
├── .flake8
├── .gitignore
└── .dockerignore
```

## Setup

### Prerequisites

- Docker & Docker Compose **or**
- Python 3.12+ and Poetry 2.x with a running PostgreSQL instance

### Run with Docker (recommended)

```bash
# 1. Clone the repository
git clone <repo-url>
cd py-theatre-api

# 2. Create the environment file
cp .env.sample .env

# 3. Build and start the services
docker-compose up --build

# 4. Create a superuser (in a separate terminal)
docker exec -it theatre python manage.py createsuperuser
```

The API will be available at `http://127.0.0.1:8000/`.

### Run locally (without Docker)

```bash
# 1. Install dependencies
poetry install

# 2. Create the environment file and adjust for local PostgreSQL
cp .env.sample .env
# Edit .env: set POSTGRES_HOST=localhost and your local DB credentials

# 3. Run migrations
poetry run python manage.py migrate

# 4. Create a superuser
poetry run python manage.py createsuperuser

# 5. Start the development server
poetry run python manage.py runserver
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `POSTGRES_DB` | Database name | `theatre` |
| `POSTGRES_USER` | Database user | `theatre` |
| `POSTGRES_PASSWORD` | Database password | `theatre` |
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `DJANGO_SECRET_KEY` | Django secret key | insecure dev key |
| `DJANGO_DEBUG` | Debug mode (`False` to disable) | `True` |

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/users/register/` | Register a new user |
| POST | `/api/users/login/` | Obtain JWT token pair |
| POST | `/api/users/refresh/` | Refresh JWT access token |
| POST | `/api/users/token/verify/` | Verify a JWT token |
| GET | `/api/users/me/` | View / update current user profile |
| PUT | `/api/users/me/` | Update current user profile |

### Documentation

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/doc/swagger/` | Swagger UI |
| GET | `/api/doc/redoc/` | ReDoc |
| GET | `/api/schema/` | OpenAPI schema (JSON) |

### Admin

| Method | Endpoint | Description |
|---|---|---|
| GET | `/admin/` | Django admin panel |

## Testing

```bash
# Run tests via Docker
docker-compose run theatre sh -c "python manage.py test"

# Run tests locally
poetry run python manage.py test

# Run flake8 linting
poetry run flake8
```
