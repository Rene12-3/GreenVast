from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_crop_yield_prediction():
  payload = {
      "crop": "Maize",
      "areaHa": 1.2,
      "county": "Kericho",
      "history": [
          {"season": "LR23", "quantity": 2400, "unit": "kg", "areaHa": 1.1},
          {"season": "SR23", "quantity": 2100, "unit": "kg", "areaHa": 1.0},
      ],
      "rainfall": 820,
      "outbreakRisk": 0.1,
  }
  resp = client.post("/predict/yield/crop", json=payload)
  assert resp.status_code == 200
  data = resp.json()
  assert data["low"] < data["mid"] < data["high"]
  assert data["unit"] == "kg"


def test_dairy_yield_prediction():
  payload = {
      "type": "Dairy",
      "headCount": 8,
      "sessionsPerDay": 2,
      "avgMilkLpd": 9.5,
      "droughtRisk": 0.1,
  }
  resp = client.post("/predict/yield/livestock", json=payload)
  assert resp.status_code == 200
  data = resp.json()
  assert data["unit"] == "litres_per_session"
  assert data["low"] < data["mid"] < data["high"]


def test_beef_yield_prediction():
  payload = {
      "type": "Beef",
      "headCount": 20,
      "droughtRisk": 0.2,
      "outbreakRisk": 0.1,
      "history": [{"headsReady": 6, "liveweightKg": 320}],
  }
  resp = client.post("/predict/yield/livestock", json=payload)
  assert resp.status_code == 200
  data = resp.json()
  assert data["headsReady"] > 0
  assert len(data["liveweightKgRange"]) == 2
