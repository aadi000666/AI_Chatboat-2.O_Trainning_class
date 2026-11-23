from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database.connection import DatabaseBase, get_database_session
from backend.main import app

test_database_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_database_engine
)

DatabaseBase.metadata.create_all(bind=test_database_engine)


def override_get_database_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_database_session] = override_get_database_session

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "online"
    assert "Secure Multimodal AI Chatbot API" in payload["service"]


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "database_connected" in payload
    assert "gemini_configured" in payload


def test_create_and_fetch_conversation():
    create_response = client.post("/conversation")
    assert create_response.status_code == 201
    created_data = create_response.json()
    conversation_id = created_data["id"]
    assert conversation_id is not None

    fetch_response = client.get(f"/conversation/{conversation_id}")
    assert fetch_response.status_code == 200
    fetched_data = fetch_response.json()
    assert fetched_data["id"] == conversation_id
    assert fetched_data["title"] == "New Conversation"


def test_chat_message_flow():
    chat_payload = {
        "message": "Hello multimodal assistant",
        "request_audio_response": False
    }
    response = client.post("/chat", json=chat_payload)
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "message_id" in data
    assert len(data["response_text"]) > 0
    assert data["processing_status"] in ("success", "failed")


def test_delete_conversation():
    create_response = client.post("/conversation")
    conversation_id = create_response.json()["id"]

    delete_response = client.delete(f"/conversation/{conversation_id}")
    assert delete_response.status_code == 200

    fetch_response = client.get(f"/conversation/{conversation_id}")
    assert fetch_response.status_code == 404
