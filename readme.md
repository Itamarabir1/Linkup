# LinkUp

Ride-sharing / carpool backend and workers: auth, rides, bookings, notifications (email, push), outbox events, and maintenance.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Running Locally](#running-locally)
- [Running with Docker](#running-with-docker)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Database Setup](#database-setup)
- [Workers](#workers)

---

## Features

- **Auth**: Register, login (JWT + refresh token), logout, refresh token, email verification (one-click link + form), password reset
- **Users**: Profile, update, FCM token
- **Rides**: Create, list, cancel; PostGIS for routes
- **Bookings & Passenger requests**: Join rides, approve/reject, maintenance (expire/complete)
- **Notifications**: Email (Brevo), push (FCM); event-driven via RabbitMQ + outbox
- **Outbox**: Reliable event dispatch (exchange + routing_key from `event_name`)
- **Maintenance**: Scheduler for expired rides, passenger requests, bookings

---

## Tech Stack

| Layer        | Stack |
|-------------|--------|
| **API**     | FastAPI, Pydantic, SQLAlchemy 2 (async + asyncpg) |
| **DB**      | PostgreSQL 15 + PostGIS |
| **Cache**   | Redis |
| **Messaging** | RabbitMQ (aio-pika), optional Kafka |
| **Email**   | Brevo (Sendinblue) |
| **Push**    | Firebase (FCM) |
| **Storage** | AWS S3 (optional) |
| **Frontend** | Vite + React (web only, in `frontend/`) |

---

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ with PostGIS
- Redis
- RabbitMQ
- Node.js 20+ (for frontend)

---

## Quick Start

1. Clone and enter the repo:
   ```bash
   cd Linkup
   ```

2. Backend: copy env and install:
   ```bash
   cd backend
   cp .env.example .env   # or create .env (see [Environment Variables](#environment-variables))
   pip install -r requirements.txt
   ```

3. Database: create DB and run schema:
   ```bash
   psql -U admin -d linkup_app -f ../db/schema.sql
   ```

4. Run API:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

5. (Optional) Run workers:
   ```bash
   python -m app.workers.main_worker
   ```

6. API: <http://localhost:8080>  
   Docs: <http://localhost:8080/docs>

---

## Environment Variables

### מקור אמת (Single source of truth)

- **בקאנד** (`backend/.env`): כל המפתחות והסודות מוגדרים כאן. העתק מ-`backend/.env.example` ומלא ערכים.
- **פרונט** (`frontend/.env`): רק כתובת ה-API (`VITE_API_URL`) וחוויית פיתוח. מפתחות שצריך בדפדפן (למשל Google Maps לתצוגת מפה) **לא** מוגדרים בפרונט – הפרונט מקבל אותם מהבקאנד דרך API (למשל `GET /api/v1/geo/maps-key`). כך יש מקור אמת אחד ומחזור מפתחות במקום אחד.

Create `backend/.env` (copy from `backend/.env.example`). Main variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (required) | `your-secret-key` |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_USER` | DB user | `admin` |
| `POSTGRES_PASSWORD` | DB password | `password123` |
| `POSTGRES_DB` | DB name | `linkup_app` |
| `REDIS_HOST` | Redis host | `localhost` |
| `RABBITMQ_HOST` | RabbitMQ host | `localhost` |
| `FRONTEND_URL` | Frontend base URL (redirects) | `https://linkup.co.il` |
| `API_PUBLIC_URL` | Public API URL (email verification link) | `https://api.linkup.co.il` |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key – Geocoding, Directions, Distance Matrix. גם נשלח לפרונט ל-Maps JavaScript API דרך `GET /api/v1/geo/maps-key`. | — |
| `FORCE_HTTPS_REDIRECT` | Redirect HTTP → HTTPS (set `true` when behind Nginx/Cloudflare) | `false` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON list or leave empty to use FRONTEND_URL) | — |
| `RATE_LIMIT_AUTH_WINDOW_SECONDS` | Rate limit window for auth endpoints (seconds) | `60` |
| `RATE_LIMIT_AUTH_MAX_REQUESTS` | Max requests per IP per window for auth | `10` |
| `BREVO_API_KEY` | Brevo API key (email) | — |
| `BREVO_SENDER_NAME` | Sender name in emails | `LinkUp` |

See `app/core/config.py` for the full list and defaults.

**Frontend** (`frontend/.env`): Copy from `frontend/.env.example`. Required: `VITE_API_URL`. Optional: `VITE_GOOGLE_MAPS_API_KEY` (only if you need to override; normally the frontend gets the Maps key from the backend).

---

## HTTPS (Production)

In production, TLS (HTTPS) is usually handled by a **reverse proxy** (Nginx, Caddy, Cloudflare) in front of the API. The proxy terminates SSL and forwards requests to the app (e.g. `http://127.0.0.1:8080`) with headers like `X-Forwarded-Proto` and `X-Forwarded-Host`.

- Set **`FORCE_HTTPS_REDIRECT=true`** in `.env` so that any HTTP request reaching the app is redirected to HTTPS (301). The app uses `X-Forwarded-Proto` to detect HTTP.
- Ensure the proxy passes `X-Forwarded-Proto: https` and `X-Forwarded-Host: your-api-domain` to the backend.
- For local development, leave `FORCE_HTTPS_REDIRECT=false` (default).

---

## Security (summary)

- **CORS**: Allowed origins from `CORS_ORIGINS` or `FRONTEND_URL`; credentials and common methods/headers allowed.
- **HTTPS**: Redirect HTTP → HTTPS when `FORCE_HTTPS_REDIRECT=true` and behind a proxy that sets `X-Forwarded-Proto`.
- **Security headers**: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` on all responses; **HSTS** (`Strict-Transport-Security`: max-age=31536000; includeSubDomains) added only when the request is over HTTPS (scheme or `X-Forwarded-Proto`).
- **Rate limiting**: Auth endpoints (login, refresh, forgot-password, password-reset/request) limited per IP via Redis (configurable window and max requests); fail-open if Redis is down.
- **Logout**: `POST /auth/logout` (with access token) clears the user’s refresh token in the DB.

---

## Running Locally

- **API only**
  ```bash
  cd backend && uvicorn app.main:app --reload --port 8080
  ```

- **Workers** (outbox, notifications, maintenance)
  ```bash
  cd backend && python -m app.workers.main_worker
  ```

- **Frontend (web)**
  ```bash
  cd frontend && npm install && npm run dev
  ```
  Then open <http://localhost:5173>. The app is Hebrew RTL (login, register, my rides, create ride, search, my requests, profile).

Ensure PostgreSQL, Redis, and RabbitMQ are running (e.g. via Docker for infra only).

---

## Running with Docker

From the project root:

```bash
docker compose up -d
```

- **API (Backend)**: <http://localhost:8000>
- **RabbitMQ management**: <http://localhost:15672> (guest/guest)
- **Chat WebSocket**: <ws://localhost:8081/ws?token=JWT>

Apply DB schema once (see [Database Setup](#database-setup)).

---

## API Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

Base path for v1: `/api/v1` (e.g. `/api/v1/auth/login`, `/api/v1/rides`).

---

## Project Structure

מבנה מונורפו – כולם תחת שורש הפרויקט; `docker-compose` והגדרות DB בשורש.

```
Linkup/
├── docker-compose.yml     # שורש – כל השירותים (db, redis, rabbitmq, backend, outbox-worker, chat-ws)
├── db/                    # שורש – סכמה ומיגרציות SQL
│   ├── schema.sql         # סכמה ראשית (להריץ פעם אחת בסביבה חדשה)
│   └── migrations/        # סקריפטי SQL לשינויים (לשמור ב-Git, להריץ לפי צורך)
├── backend/
│   ├── app/
│   │   ├── main.py        # נקודת כניסה ל-API (uvicorn app.main:app)
│   │   ├── api/           # Routers, dependencies
│   │   ├── core/          # Config, security, exceptions, lifespan
│   │   ├── db/            # Session, base
│   │   ├── domain/        # Auth, users, rides, bookings, passengers, notifications, events
│   │   ├── infrastructure/# Outbox, RabbitMQ, Redis, S3
│   │   └── workers/       # Outbox worker, notification/maintenance tasks
│   ├── alembic/           # מיגרציות Python (Alembic) – היסטוריית שינויים, לשמור ב-Git
│   └── requirements.txt
├── frontend/              # Web (Vite + React, RTL Hebrew)
├── mobile/                # אפליקציית מובייל (Expo)
└── chat-ws/               # שרת WebSocket לצ'אט (Go)
```

- **docker-compose** – בשורש, כדי להריץ את כל המערכת (DB, backend, workers, chat) בפקודה אחת.
- **main** – נמצא ב-`backend/app/main.py` (לא בתיקייה נפרדת "main").
- **migrations** – `db/migrations/` ו-`backend/alembic/` נשארים ב-repo: מריצים אותם פעם (או בכל סביבה), אבל הקבצים עצמם נשמרים כדי שכל מי שמשכפל יוכל להריץ את אותן מיגרציות.

---

## Database Setup

1. Create the database (if not exists):
   ```bash
   createdb -U admin linkup_app
   ```

2. Apply schema (creates tables and enums):
   ```bash
   psql -U admin -d linkup_app -f db/schema.sql
   ```

3. For Docker Postgres, run the same from host or from a one-off container:
   ```bash
   docker exec -i linkup_db psql -U admin -d linkup_app < db/schema.sql
   ```

If tables like `bookings` or `passenger_requests` are missing, maintenance and related features will log warnings until the schema is applied.

---

## Event metadata (exchange + routing_key)

- **מקור אמת**: `domain/events/routing.py` – `get_routing_metadata(event_name)` מחזיר `exchange` ו-`routing_key`.
- **exchange** = דומיין (user, ride, booking) – כל המשימות שקשורות למשתמש (מייל רישום, אימות, איפוס סיסמה) יוצאות ל-exchange `"user"`.
- **routing_key** = `event_name` – כל משימה מקבלת מפתח ייחודי (למשל `auth.email_verification`, `user.registered`). ה-handler מזהה לפי ה-routing_key איזה לוגיקה להריץ.
- **תור אחד + וורקר אחד**: `notifications_queue` מקושר לכל ה-exchanges (user, ride, booking, system_events). וורקר אחד מקבל את כל ההודעות; ה-`routing_key` שבכל הודעה קובע איזה handler (מייל/פוש) להפעיל. אין צורך בתור נפרד לכל סוג מייל.

השירותים (למשל auth) כותבים לאוטבוקס רק `event_name` + `payload`; ה-metadata מתווסף אוטומטית בעת העיבוד ב-OutboxService.

---

## Workers

- **Outbox worker**: קורא אירועים ממתינים מ-`outbox_events`, בונה `Event` עם metadata מ-`get_routing_metadata(event_name)`, שולח ל-RabbitMQ (exchange + routing_key).
- **Notification consumer**: מקשיב ל-`notifications_queue` (מקושר ל-user, ride, booking, system_events). מטפל באירועים לפי `routing_key` (למשל `auth.email_verification`, `user.registered`) – שולח מייל/פוש לפי המפות.
- **Maintenance scheduler**: מעדכן נסיעות/בקשות/הזמנות שפג תוקף (דורש טבלאות ו-enums ב-DB).

---

## License

Private / proprietary unless otherwise stated.
