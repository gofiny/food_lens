from fastapi.testclient import TestClient


def test_healthcheck(client: TestClient):
    response = client.get("/health_check")
    assert response.status_code == 200
