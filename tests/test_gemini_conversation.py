from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database.connection import DatabaseBase
from backend.database.crud import (
    create_conversation,
    create_message,
    get_conversation_messages
)
from backend.schemas.chat_schema import ChatRequest
from backend.services.ai_engine import ai_engine
from backend.services.conversation_service import conversation_service
from backend.services.gemini_service import GeminiServiceException, gemini_service

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

DatabaseBase.metadata.create_all(bind=test_engine)


def test_conversation_service_turn_formatting():
    session = TestingSessionLocal()
    conv = create_conversation(session, title="New Conversation")
    create_message(session, conv.id, "user", "What is the capital of France?")
    create_message(session, conv.id, "assistant", "The capital of France is Paris.")

    formatted_turns = conversation_service.format_history_for_gemini(session, conv.id)
    assert len(formatted_turns) == 2
    assert formatted_turns[0].role == "user"
    assert formatted_turns[1].role == "model"
    assert formatted_turns[0].parts[0].text == "What is the capital of France?"

    conversation_service.update_conversation_title_if_default(session, conv.id, "What is the capital of France?")
    session.refresh(conv)
    assert conv.title == "What is the capital of France?"
    session.close()


def test_ai_engine_multi_turn_with_gemini_service():
    session = TestingSessionLocal()

    with patch.object(gemini_service, "generate_chat_response") as mock_generate:
        mock_generate.side_effect = [
            "I will remember your keyword PHOENIX99.",
            "Your secret keyword is PHOENIX99."
        ]

        first_request = ChatRequest(message="My secret keyword is PHOENIX99.")
        first_response = ai_engine.process_chat(first_request, session)

        assert first_response.conversation_id is not None
        assert "PHOENIX99" in first_response.response_text
        assert first_response.processing_status == "success"

        active_id = first_response.conversation_id

        second_request = ChatRequest(
            conversation_id=active_id,
            message="What is my secret keyword?"
        )
        second_response = ai_engine.process_chat(second_request, session)

        assert "PHOENIX99" in second_response.response_text
        assert second_response.processing_status == "success"

        messages = get_conversation_messages(session, active_id)
        assert len(messages) == 4
        assert messages[0].content == "My secret keyword is PHOENIX99."
        assert messages[1].content == "I will remember your keyword PHOENIX99."
        assert messages[2].content == "What is my secret keyword?"
        assert messages[3].content == "Your secret keyword is PHOENIX99."

    session.close()


def test_ai_engine_handles_gemini_failure_gracefully():
    session = TestingSessionLocal()

    with patch.object(gemini_service, "generate_chat_response") as mock_generate:
        mock_generate.side_effect = GeminiServiceException("API connection timeout")

        request = ChatRequest(message="Test failure scenario")
        response = ai_engine.process_chat(request, session)

        assert response.processing_status == "failed"
        assert "Gemini Error: API connection timeout" in response.response_text

        messages = get_conversation_messages(session, response.conversation_id)
        assert len(messages) == 2
        assert messages[1].sender_role == "assistant"

    session.close()
