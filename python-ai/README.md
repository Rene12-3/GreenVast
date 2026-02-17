# GreenVast Python AI Service

This FastAPI microservice provides lightweight AI helpers for the NestJS backend:

- Price baseline training and inference (`/train/price`, `/predict/price`)
- Crop and livestock yield ranges (`/predict/yield/crop`, `/predict/yield/livestock`)
- Weather-to-action advisory helper (`/advisory`)
- Health checks (`/health`)

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Tests

```bash
pytest
```

## Endpoints (dev)

- `GET /health` – service heartbeat
- `POST /train/price` – load price snapshots for inference
- `POST /predict/price` – infer price for commodity/market pair
- `POST /predict/yield/crop` – estimate crop yield range
- `POST /predict/yield/livestock` – estimate dairy or beef outcomes
- `POST /advisory` – generate low-literacy advisory messages from forecast snippets

All prediction endpoints return a `modelVersion` field for traceability.
