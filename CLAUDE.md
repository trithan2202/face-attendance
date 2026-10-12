# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Local face-recognition attendance system (student thesis project): a browser kiosk that recognises employees via webcam and records check-in/check-out, plus an admin SPA for employees, departments, shifts, leave requests, attendance adjustments (with audit trail), runtime settings and Excel reports. User-facing strings (API error messages, UI text) are in Vietnamese — keep new ones in Vietnamese.

## Commands

Windows + PowerShell is the primary dev environment. Python deps live in `.venv` (Python 3.11 in Docker). All Python entry points are run as modules from the repo root (`python -m ...`) because packages import each other by top-level name (`backend.app...`, `attendance...`, `face_engine...`).

```powershell
# Full stack (Postgres + backend + nginx frontend) — recommended for demo
docker compose up -d --build        # frontend :3000, API :8000 (/api/docs), Postgres :5432

# Local dev (needs Postgres reachable via DATABASE_URL in .env)
.\scripts\migrate.ps1               # = python -m scripts.bootstrap_db : alembic upgrade head + seed shift/department/admin/settings
.\scripts\run_api.ps1               # uvicorn backend.app.main:app --reload on 127.0.0.1:8000
.\scripts\run_frontend.ps1          # vite dev on :5173, proxies /api -> 127.0.0.1:8000
.\scripts\run_recognition_worker.ps1  # optional desktop OpenCV worker (camera/), not used by the browser kiosk

# Migrations
.\.venv\Scripts\python.exe -m alembic revision -m "msg"   # files in migrations/versions, named YYYYMMDD_NNNN_*.py
.\.venv\Scripts\python.exe -m alembic upgrade head

# Tests (stdlib unittest; API tests use FastAPI TestClient + in-memory SQLite, no Postgres needed)
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m unittest tests.test_attendance_api
.\.venv\Scripts\python.exe -m unittest tests.test_attendance_api.AttendanceApiTests.<test_name>

# Frontend
cd frontend; npm install; npm run build
```

Notes:
- `tests/`, `docs/`, `PROJECT_STATUS.md` and `SYSTEM_DIAGRAMS.md` exist locally but are **gitignored** — edits there are not committed.
- `frontend` has an `npm run lint` script but no ESLint config file is checked in.
- First backend start downloads the InsightFace `buffalo_l` model (~280 MB) into `~/.insightface` (a named volume in Docker).

## Architecture

Three Python top-level packages plus the FastAPI app, all importable from the repo root:

- `face_engine/` — pure CV layer: InsightFace detection/embedding (`engine.py`, `detector.py`, `recognizer.py`), CLAHE/brightness preprocessing (`preprocess.py`), quality checks, and `FaceMatcher` (cosine similarity against per-employee **centroid** embeddings).
- `attendance/` — attendance domain logic, independent of HTTP. `WorkDateResolver` maps a scan to a work date (cross-day shifts: scans before `shift.end_time` belong to the previous day). `AttendanceCalculator` computes late/early/overtime and `recalculate()` rebuilds a daily row after adjustments. `AttendanceService.process()` decides check-in vs check-out and returns a "suppressed" result with a reason code (`DUPLICATE_PUNCH`, `TOO_EARLY_CHECKOUT`, `SHIFT_MISSING`, …) instead of raising.
- `camera/` — optional standalone desktop worker (OpenCV capture + stabilizer) that writes heartbeat to `WORKER_STATUS_FILE`; the API exposes it at `/api/worker/status`.
- `backend/app/` — FastAPI layered as `api/` (routers) → `services/` → `repositories/` (static-method SQLAlchemy queries) → `models/`; `schemas/` are Pydantic. `main.py` registers all routers under `/api`, adds request-id JSON logging middleware, and normalises every error to `{code, message, details}`.

### Key flows

- **Kiosk recognition** (`api/kiosk.py` → `services/recognition.py`): browser starts a session (loads all centroids from DB), then POSTs frames to `/api/kiosk/recognition/{id}/frame`. Exactly one face must match the same employee continuously for `RECOGNITION_HOLD_SECONDS` (frame gaps > `RECOGNITION_MAX_FRAME_GAP_SECONDS` reset the timer) before `AttendanceService` records an event. No auth, no liveness on the kiosk.
- **Enrollment** (`api/admin/enrollment.py` → `services/enrollment.py`): admin-only; requires a MediaPipe liveness challenge (blink/head turn, `services/liveness.py`) and then captures multiple embeddings stored in `face_embeddings` (binary via `core/embedding_codec.py`). No images are persisted.
- Recognition, enrollment and liveness sessions are **in-memory** singletons guarded by locks — they vanish on restart and assume a single backend process.
- `services/face_engine_provider.get_face_engine()` is a lazily created process-wide singleton (warmed up in a background thread at startup when `FACE_ENGINE_WARMUP=true`). Services take an `engine_factory` arg so tests can inject fakes — use this instead of loading the real model in tests.

### Configuration

- `backend/app/core/config.py` reads `.env` into a plain `Settings` object (not pydantic-settings); see `.env.example` for all keys.
- A subset of thresholds (`EDITABLE_SETTINGS` in `services/settings_service.py`: similarity threshold, hold seconds, min checkout/punch interval, overtime minimum, half-day ratio) can be overridden at runtime from the admin Settings page via the `system_settings` table; services re-read them per request/frame, so DB values win over `.env`. New runtime-editable settings must be added there and seeded in `scripts/seed_system_settings.py`.

### Database

PostgreSQL 16 via SQLAlchemy 2 (`psycopg` driver); schema owned by Alembic (`migrations/`). `scripts/bootstrap_db.py` also adopts a legacy pre-Alembic schema by stamping revision `20260813_0001`. Models must also work on SQLite because the API tests build the schema with `Base.metadata.create_all` on an in-memory SQLite engine and override `get_db`.

### Frontend

React 18 + Vite + Tailwind, plain JSX. `src/services/api.js` is the single fetch wrapper (`credentials: 'include'` — auth is a JWT in an HttpOnly cookie, see `contexts/AuthContext.jsx`). Routes: `/kiosk`, `/login`, `/tra-cuu` (public attendance lookup by employee code), `/admin/*`. Shared primitives live in `src/components/ui/`. In Docker, `frontend/nginx.conf` serves the build and proxies `/api` to the backend.
