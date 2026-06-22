from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_response():
    payload = {
        "message": "Bonjour, je veux comprendre comment dimensionner une installation solaire.",
        "session_id": "test-chat-session",
        "user_id": None,
        "context": None
    }

    response = client.post("/api/v1/chat/", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "response" in data
    assert "session_id" in data
    assert "suggested_questions" in data
    assert isinstance(data["suggested_questions"], list)


def test_get_chat_history():
    response = client.get("/api/v1/chat/history")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_clear_chat_history():
    response = client.delete("/api/v1/chat/history")

    assert response.status_code == 200

    data = response.json()

    assert "success" in data
    assert "message" in data