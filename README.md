# fancy-todos

FastAPI + SQLModel + Postgres + Alembic. Auth via JWT.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker (for Postgres)

## First-time setup

```bash
# 1. install deps into a local .venv
uv sync

# 2. copy the env template and edit secrets
cp .env.example .env
# open .env and set at minimum:
#   SECRET_KEY              (generate: openssl rand -hex 32)
#   FIRST_SUPERUSER_EMAIL
#   FIRST_SUPERUSER_PASSWORD

# 3. start Postgres
docker compose up -d

# 4. apply migrations
uv run alembic upgrade head

# 5. (optional) seed the first superuser from .env
uv run python -c "from sqlmodel import Session; from app.core.db import engine, init_db; init_db(Session(engine))"
```

## Running the dev server

```bash
uv run fastapi dev app/main.py
```

The API is served at `http://127.0.0.1:8000` under the prefix `/api/v1`. The server auto-reloads on file changes.

## Testing the API via OpenAPI / Swagger

FastAPI ships an interactive API explorer. With the dev server running, open:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI schema (JSON)**: http://127.0.0.1:8000/api/v1/openapi.json

Typical flow in Swagger:

1. `POST /api/v1/users/signup` — create a user.
2. `POST /api/v1/login/access-token` — log in (form fields: `username` = email, `password`). Copy the `access_token`.
3. Click the **Authorize** button (top right), paste the token, hit Authorize. All subsequent calls will include the bearer header.
4. Try `GET /api/v1/users/me`, `POST /api/v1/todos/`, `GET /api/v1/todos/`, etc.

## Database migrations

After changing or adding a model in [app/models/](app/models/):

```bash
# generate a new migration from the diff between models and DB
uv run alembic revision --autogenerate -m "describe the change"

# review the generated file in app/alembic/versions/, then apply
uv run alembic upgrade head
```

Other useful commands:

```bash
uv run alembic current        # which revision is applied
uv run alembic history        # full revision history
uv run alembic downgrade -1   # roll back one revision
```

## Project layout

```
app/
├── main.py                # FastAPI app + router mount
├── api/
│   ├── main.py            # router aggregator
│   ├── deps.py            # SessionDep, CurrentUser, superuser guard
│   └── routes/            # login, users, todos, utils
├── core/
│   ├── config.py          # pydantic-settings (.env driven)
│   ├── db.py              # engine + init_db
│   └── security.py        # bcrypt + JWT helpers
├── models/                # SQLModel tables + Pydantic schemas
├── crud/                  # data access (crud.user.*, crud.todo.*)
└── alembic/               # migrations
```

## Stopping

```bash
# stop the dev server: Ctrl+C
docker compose down          # stop Postgres (keeps volume)
docker compose down -v       # also wipe the database volume
```
