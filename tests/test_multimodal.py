import io
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database.connection import DatabaseBase
from backend.database.crud import create_conversation, record_uploaded_file
from backend.processors.audio_processor import AudioProcessorException, audio_processor
from backend.processors.image_processor import ImageProcessorException, image_processor
from backend.schemas.chat_schema import ChatRequest
from backend.services.ai_engine import ai_engine
from backend.services.gemini_service import gemini_service

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


def create_synthetic_png_bytes(width: int = 100, height: int = 100) -> bytes:
    image = Image.new("RGB", (width, height), color=(73, 109, 137))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_image_processor_valid_and_invalid():
    png_bytes = create_synthetic_png_bytes()
    img_format, w, h = image_processor.validate_and_inspect_image(png_bytes)
    assert img_format == "PNG"
    assert w == 100
    assert h == 100

    with pytest.raises(ImageProcessorException):
        image_processor.validate_and_inspect_image(b"not an image data")


def test_audio_processor_validation():
    valid_mime = audio_processor.validate_audio_file("voice.wav", b"dummy_audio_bytes")
    assert valid_mime == "audio/wav"

    with pytest.raises(AudioProcessorException):
        audio_processor.validate_audio_file("document.pdf", b"bytes")

    with pytest.raises(AudioProcessorException):
        audio_processor.validate_audio_file("voice.mp3", b"")


def test_text_to_speech_synthesis():
    sample_text = "Testing multimodal text to speech synthesis."

    def fake_write_to_fp(fp):
        fp.write(b"MOCK_MP3_AUDIO_STREAM_DATA")

    with patch("backend.processors.audio_processor.gTTS") as mock_gtts_cls:
        mock_instance = MagicMock()
        mock_instance.write_to_fp.side_effect = fake_write_to_fp
        mock_gtts_cls.return_value = mock_instance

        encoded_audio = audio_processor.synthesize_speech_to_base64(sample_text)
        assert isinstance(encoded_audio, str)
        assert len(encoded_audio) > 10


def test_ai_engine_with_image_attachment():
    session = TestingSessionLocal()
    conv = create_conversation(session, title="Multimodal Image Test")

    with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".png") as temp_img:
        temp_img.write(create_synthetic_png_bytes())
        temp_img_path = Path(temp_img.name)

    try:
        file_record = record_uploaded_file(
            session=session,
            conversation_id=conv.id,
            original_filename="test_graph.png",
            stored_filename=temp_img_path.name,
            file_type="image",
            mime_type="image/png",
            file_size_bytes=temp_img_path.stat().st_size,
            storage_path=str(temp_img_path)
        )

        with patch.object(gemini_service, "generate_chat_response", return_value="The image shows a solid blue square."):
            request = ChatRequest(
                conversation_id=conv.id,
                message="What does this image show?",
                attached_file_ids=[file_record.id]
            )
            response = ai_engine.process_chat(request, session)

            assert response.response_type == "multimodal"
            assert "solid blue square" in response.response_text
            assert response.processing_status == "success"
    finally:
        if temp_img_path.exists():
            temp_img_path.unlink()
        session.close()


def test_ai_engine_with_audio_tts_request():
    session = TestingSessionLocal()
    conv = create_conversation(session, title="TTS Request Test")

    with patch.object(gemini_service, "generate_chat_response", return_value="Here is your spoken response."):
        with patch.object(audio_processor, "synthesize_speech_to_base64", return_value="UklGRi4AAABXQVZFZm10IBAAAAABAAEA"):
            request = ChatRequest(
                conversation_id=conv.id,
                message="Please speak your answer.",
                request_audio_response=True
            )
            response = ai_engine.process_chat(request, session)

            assert response.audio_output == "UklGRi4AAABXQVZFZm10IBAAAAABAAEA"
            assert response.response_type == "audio"
            assert "Here is your spoken response." in response.response_text

    session.close()
