from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_health_endpoint():
  response = client.get("/health")
  assert response.status_code == 200
  data = response.json()
  assert data["ok"] is True
  assert data["service"] == "python-ai"
