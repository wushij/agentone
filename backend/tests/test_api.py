"""tests/test_api.py — API 测试"""

from fastapi.testclient import TestClient


class TestHealth:
    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_public_settings(self, client: TestClient):
        response = client.get("/api/settings/public")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200


class TestAuth:
    def test_login_without_credentials(self, client: TestClient):
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 422

    def test_register_validation(self, client: TestClient):
        response = client.post("/api/auth/register", json={})
        assert response.status_code == 422