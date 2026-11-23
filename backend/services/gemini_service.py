import os
from typing import Any, List, Optional
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from backend.config import application_settings


class GeminiServiceException(Exception):
    pass


class GeminiService:
    def __init__(self):
        self.api_key = (
            application_settings.GEMINI_API_KEY
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        self.model_name = application_settings.GEMINI_MODEL
        self.embedding_model = application_settings.EMBEDDING_MODEL
        self.client = self._initialize_client()

    def _initialize_client(self) -> genai.Client:
        if self.api_key:
            return genai.Client(api_key=self.api_key)
        return genai.Client()

    def generate_chat_response(
        self,
        contents: List[Any],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        try:
            config = types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_instruction
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            return response.text or ""
        except ClientError as error:
            error_msg = str(error)
            if "leaked" in error_msg.lower() or "permission_denied" in error_msg.lower():
                raise GeminiServiceException(
                    "The configured Gemini API key has been revoked by Google (reported as leaked). "
                    "Please provide a fresh GEMINI_API_KEY in your .env file from Google AI Studio."
                )
            raise GeminiServiceException(f"Gemini API Client Error: {error_msg}")
        except ServerError as error:
            raise GeminiServiceException(f"Gemini API Server Error: {str(error)}")
        except Exception as error:
            raise GeminiServiceException(f"Gemini Generation Error: {str(error)}")

    def generate_embedding(self, text_chunk: str) -> List[float]:
        try:
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text_chunk
            )
            if response.embeddings and len(response.embeddings) > 0:
                return response.embeddings[0].values
            return []
        except ClientError as error:
            error_msg = str(error)
            if "leaked" in error_msg.lower() or "permission_denied" in error_msg.lower():
                raise GeminiServiceException(
                    "The configured Gemini API key has been revoked by Google. "
                    "Please provide a fresh GEMINI_API_KEY in your .env file."
                )
            raise GeminiServiceException(f"Gemini API Client Error: {error_msg}")
        except ServerError as error:
            raise GeminiServiceException(f"Gemini API Server Error: {str(error)}")
        except Exception as error:
            raise GeminiServiceException(f"Gemini Embedding Error: {str(error)}")


gemini_service = GeminiService()
