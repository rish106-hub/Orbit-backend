# Orbit Backend

Standalone FastAPI backend for Orbit Calendar.

## Stack
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL / Neon

## Local Setup
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

## Environment
Required:
- `DATABASE_URL`

Optional:
- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `CALENDAR_PROVIDER`

## Hosted Deployment
This repo now includes:
- `Dockerfile` for container-based hosts
- `.dockerignore` for clean container builds
- `render.yaml` as a simple managed-host template

Generic start command:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Notes
- Set `DATABASE_URL` to your Neon connection string in `.env` or host secrets
- The macOS app can point to this backend via the in-app backend URL setting or `ORBIT_API_BASE_URL`
- Google OAuth is intentionally not wired yet
