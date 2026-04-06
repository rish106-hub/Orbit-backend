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

## Notes
- Set `DATABASE_URL` to your Neon connection string in `.env`
- The macOS app can point to this backend via `ORBIT_API_BASE_URL`
