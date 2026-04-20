# Network Testing Dashboard

This workspace is now reduced to one backend job: store raw MQTT messages in PostgreSQL.
The frontend is a static landing page and the backend exposes one dummy API endpoint at `/api/dummy`.

## What remains

- FastAPI backend
- PostgreSQL storage for `mqtt_messages`
- MQTT worker that writes raw messages to the database
- Minimal React + Vite front page

## Run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.mqtt_worker
```

## Hard reset DB (data loss)

If your database points to a missing revision (for example, "Can't locate revision"),
you can wipe the schema and rebuild migrations from scratch:

```bash
cd backend
.venv\Scripts\activate
python reset_db_and_migrate.py
```

```bash
cd frontend
npm install
npm run dev
```

Use your online MQTT broker details in [backend/.env.example](backend/.env.example).