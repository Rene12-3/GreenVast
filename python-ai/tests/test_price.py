from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def _snapshot(day_offset: int, price: float):
  base = datetime.utcnow().date()
  date = datetime.combine(base - timedelta(days=7 * day_offset), datetime.min.time())
  return {
      "commodity": "Maize",
      "market": "Kericho",
      "date": date.isoformat(),
      "unit": "kg",
      "avgPrice": price,
  }


def test_train_and_predict_price():
  train_payload = {"rows": [_snapshot(idx, 32 + idx) for idx in range(4)]}
  train_resp = client.post("/train/price", json=train_payload)
  assert train_resp.status_code == 200
  assert train_resp.json()["pairs"] == 1

  predict_resp = client.post(
      "/predict/price", json={"commodity": "Maize", "market": "Kericho"}
  )
  assert predict_resp.status_code == 200
  body = predict_resp.json()
  assert "price" in body
  assert body["unit"] == "kg"
  assert 0.2 <= body["confidence"] <= 0.9
