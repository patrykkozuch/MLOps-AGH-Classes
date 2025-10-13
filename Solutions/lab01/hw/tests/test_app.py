import pytest

from fastapi.testclient import TestClient
from sa.app import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_empty_input(client):
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 400
    assert response.json() == {"detail": "Text cannot be empty"}


def test_valid_input(client):
    response = client.post("/predict", json={"text": "I love programming!"})
    assert response.status_code == 200
    assert "prediction" in response.json()
    assert response.json()["prediction"] == "positive"
