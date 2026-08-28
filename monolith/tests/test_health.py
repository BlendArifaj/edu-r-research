from fastapi.testclient import TestClient


def test_health_declares_reconstruction(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["system"] == "SEMS-R"
    assert body["integrity"] == "reconstruction_not_original_sems"


def test_openapi_title_is_reconstruction(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    assert "Reconstructed" in spec["info"]["title"]
    assert "not the original production SEMS" in spec["info"]["description"]


def test_login_rejects_bad_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": "admin@sems-r.local", "password": "wrong"}
    )
    assert response.status_code == 401
