import base64
import io
from pathlib import Path
from google.genai import types
from gtts import gTTS


class AudioProcessorException(Exception):
    pass


class AudioProcessor:
    SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg"}
    MIME_MAPPING = {
        ".wav": "audio/wav",
        ".mp3": "audio/mp3",
        ".m4a": "audio/m4a",
        ".ogg": "audio/ogg"
    }

    def validate_audio_file(self, filename: str, file_bytes: bytes) -> str:
        extension = Path(filename).suffix.lower()
        if extension not in self.SUPPORTED_AUDIO_EXTENSIONS:
            raise AudioProcessorException(f"Unsupported audio format: {extension}")

        if len(file_bytes) == 0:
            raise AudioProcessorException("Uploaded audio file is empty.")

        return self.MIME_MAPPING.get(extension, "audio/mp3")

    def build_gemini_audio_part(self, file_path: Path, mime_type: str) -> types.Part:
        if not file_path.exists():
            raise AudioProcessorException(f"Audio file does not exist at {file_path}")

        with open(file_path, "rb") as stream:
            audio_bytes = stream.read()

        return types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

    def synthesize_speech_to_base64(self, text: str, language: str = "en") -> str:
        if not text or not text.strip():
            return ""

        clean_text = text.replace("*", "").replace("#", "").strip()[:500]
        output_buffer = io.BytesIO()
        try:
            tts = gTTS(text=clean_text, lang=language, slow=False)
            tts.write_to_fp(output_buffer)
            output_buffer.seek(0)
            return base64.b64encode(output_buffer.read()).decode("utf-8")
        except Exception as error:
            raise AudioProcessorException(f"Speech synthesis error: {str(error)}")


audio_processor = AudioProcessor()
