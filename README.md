# GreenVast Backend

GreenVast backend powers the low-literacy farmer experience (prices, advisory, communities, marketplace, loans, analytics) backed by NestJS + Prisma, with optional AI helpers served by a Python FastAPI sidecar.

## Stack

- **Runtime:** Node.js 22 (NestJS 11) plus Python FastAPI microservice (`../python-ai`)
- **Database:** PostgreSQL via Prisma ORM
- **Cache/Jobs:** Redis + BullMQ, cron via `@nestjs/schedule`
- **Auth:** Firebase phone auth (ID token validation via Firebase Admin)
- **Messaging:** Socket.IO gateway for listing chat threads
- **Storage:** S3/Supabase-compatible presigned uploads
- **Integrations:** KAMIS commodity prices, OpenWeather One Call, external AI via `PYTHON_SVC_URL`
- **Localization:** JSON bundles (EN/SW) served via `/v1/i18n/:locale`

## Getting Started

```bash
cp .env.example .env                     # update connection + API keys
npm install
npm run prisma:generate
npm run prisma:migrate                   # first run: creates schema (interactive)
npm run db:seed                          # optional demo data
npm run start:dev                        # -> http://localhost:4000/api
```

Set `DATABASE_URL` to a PostgreSQL instance (Docker recommended) and `REDIS_*` for job queues. Firebase credentials are optional for local work (guard can fall back to a dev user).

## Core Modules & Endpoints

- `GET /v1/health` - service heartbeat
- **Users** `/v1/users/*` - profile sync, consent, export/delete
- **Farms** `/v1/farms/*` - parcels, crops, livestock, inventory
- **Prices** `/v1/prices`, `/v1/markets` - weekly medians from KAMIS cache
- **Advisory** `/v1/advisory?farmId=` - weather-to-action summaries (EN/SW)
- **Communities** `/v1/communities/*` - join/post/report crop+county rooms
- **Marketplace** `/v1/listings`, `/v1/offers`, `/v1/rfq` - listings, offers, RFQs, chat via WS `/chat`
- **Loans** `/v1/loans/*` - loan tracker + repayment ledger
- **Net worth** `/v1/farmer/:id/networth` - consent-aware share link
- **Storage** `/v1/storage/upload-url` - presigned S3 uploads
- **Admin** `/v1/admin/*` - report queue, moderation, analytics snapshot
- **Localization** `/v1/i18n/en|sw` - translation bundles for the app shell
- **Prediction** `/v1/prediction/*` - proxy endpoints for Python AI (price, yield/crop, yield/livestock, train/price)

All authenticated routes expect `Authorization: Bearer <FirebaseIDToken>`; `/prediction/train/price` also requires role `ADMIN`.

## Background Jobs

- `KamisService` cron (06:00 EAT) refreshes commodity medians
- Advisory lookups cache OpenWeather forecasts into `WeatherDaily`/`Advisory`
- BullMQ preconfigured for future async jobs (notifications, analytics)

## Database Notes

See `prisma/schema.prisma` for full relations (users, farms, parcels, livestock, inventory, communities, marketplace, RFQs, advisories, yield history, price snapshots, etc.).

`npm run db:seed` seeds:

- Six staple crops × five counties communities
- Eight major markets with sample KAMIS-style price snapshots (median/min/max/avg)
- Demo farmer (`firebaseUid=demo-farmer`) with parcels, dairy herd, inventory, and yield history rows (crop + milk)

## Testing & Tooling

- `npm run build`
- `npm test` (unit specs, including mocked prediction controller)
- `npm run test:e2e`
- Swagger at `/api/docs`

## AI Microservice (`../python-ai`)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
pytest
```

Exposes:
- `GET /health`
- `POST /train/price`
- `POST /predict/price`
- `POST /predict/yield/crop`
- `POST /predict/yield/livestock`
- `POST /advisory`

Responses include `modelVersion` for traceability.

## Docker Compose (dev)

```bash
PYTHON_SVC_URL=http://python-ai:8000 docker-compose up --build
```

Brings up Postgres, Redis, NestJS (port 4000), and python-ai (port 8000) with live code mounts for local iteration.

## Debug Headers

During development you can impersonate users via:

```
-H "x-debug-uid: farmer-1"
```

The same header can be used to exercise prediction routes before the mobile app is wired up.
