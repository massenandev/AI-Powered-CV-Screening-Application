from fastapi.testclient import TestClient

from app.main import app


def test_liveness() -> None:
    response = TestClient(app).get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_validation_error_shape() -> None:
    response = TestClient(app).post(
        "/api/v1/conversations/not-a-uuid/messages", json={"question": ""}
    )
    assert response.status_code == 422
    assert set(response.json()["error"]) == {"code", "message", "request_id", "details"}
