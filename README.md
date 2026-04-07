# Network Testing Dashboard Monorepo

Full-stack monorepo for capturing and analyzing Meshtastic traffic over MQTT.

Core stack:
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- MQTT ingestion (Paho)
- React + Vite + TypeScript

## Data model highlights

This schema intentionally preserves two layers of MQTT history:

1. Raw MQTT message envelope (`mqtt_messages`)
2. Parsed logical Meshtastic packet (`logical_packets`) with per-message observations (`packet_observations`)

This supports:
- Full retention of raw payloads for every MQTT message
- Parsing inner JSON packet payload when possible
- Preserving `/e/` topic data even if not parseable
- Duplicate and retransmission analysis using observation history
- Non-unique inner packet ids (no global uniqueness assumption)

## Repository layout

```
backend/
	alembic.ini
	requirements.txt
	alembic/
		env.py
		script.py.mako
		versions/
			20260407_0001_initial.py
	app/
		main.py
		mqtt_worker.py
		api/routes.py
		core/config.py
		db/base.py
		db/session.py
		models/base.py
		models/entities.py
		services/parser.py
		services/ingestion.py

frontend/
	package.json
	vite.config.ts
	index.html
	src/
		main.tsx
		App.tsx
		api.ts
		types.ts
		styles.css
```

## Quick start

### 1. Start dependencies

Use Docker to start PostgreSQL:

```
docker compose up -d
```

If you already run PostgreSQL on host port 5432, this compose file maps the container to 5434 by default.

For MQTT, configure your online broker in backend/.env.

### 2. Backend setup

```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

When using the compose PostgreSQL container, set DATABASE_URL in backend/.env to use port 5433.

### 3. Run MQTT ingestion worker

In a second terminal:

```
cd backend
.venv\Scripts\activate
python -m app.mqtt_worker
```

### 4. Frontend setup

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## API overview

- `POST /api/ingest` manual ingestion endpoint
- `GET /api/metrics` aggregate dashboard metrics
- `GET /api/nodes/stats` node-level packet statistics
- `GET /api/messages/recent` recent raw MQTT envelope messages
- `GET /api/packets/search` packet search with filters
- `GET /api/packets/{packet_id}/path` traceroute/path detail
- `GET /api/packets/duplicates` duplicate/retransmission view

## Notes

- `mqtt_messages` always stores raw payload and envelope metadata.
- If inner packet parsing fails, the message is still retained.
- `/e/` topic payloads are preserved even when unparseable.
- Duplicates are represented as multiple `packet_observations` for a single `logical_packet` fingerprint.