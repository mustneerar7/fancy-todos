# fancy-todos

Simplified starter app using FastAPI + SQLModel + Postgres + Alembic. Auth via JWT.

## First-time setup

```bash
uv sync

cp .env.example .env
docker compose up -d

make prestart
```

Run `make help` to see all available targets.

## Running the dev server

```bash
make dev
```

The API is served at `http://127.0.0.1:8000` under the prefix `/api/v1`. The server auto-reloads on file changes.

## Testing the API via OpenAPI / Swagger

FastAPI ships an interactive API explorer. With the dev server running, open:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI schema (JSON)**: http://127.0.0.1:8000/api/v1/openapi.json

## Database migrations

After changing or adding a model in [app/models/](app/models/):

```bash
# generate a new migration
make migrate m="describe the change"

# updates the database to latest migration
make upgrade
```

## Code quality

```bash
make format    # auto-fix lint issues and format
make lint      # check only — used by CI
```

## Project layout

```
app/
├── main.py
├── api/
│   ├── main.py
│   ├── deps.py
│   └── routes/
├── core/
│   ├── config.py
│   ├── db.py
│   └── security.py
├── models/
├── crud/
└── alembic/
```

## Using as a template

To spin up a new project from this one:

```bash
./scripts/new-project.sh <new-name> <destination-dir>
```

## Stopping

```bash
docker compose down
# or
docker compose down -v
```
