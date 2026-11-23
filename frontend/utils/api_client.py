import os
from typing import Any, Dict, List, Optional
import requests

DEFAULT_BACKEND_URL = os.environ.get("BACKEND_API_BASE_URL", "http://127.0.0.1:8000")


class ApiClient:
    def __init__(self, base_url: str = DEFAULT_BACKEND_URL):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as error:
            return {
                "status": "unreachable",
                "database_connected": False,
                "gemini_configured": False,
                "error": str(error)
            }

    def send_chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        request_audio_response: bool = False,
        attached_file_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        payload = {
            "conversation_id": conversation_id,
            "message": message,
            "request_audio_response": request_audio_response,
            "attached_file_ids": attached_file_ids or []
        }
        response = requests.post(f"{self.base_url}/chat", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()

    def upload_media(
        self,
        file_bytes: bytes,
        filename: str,
        media_type: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/upload/{media_type}"
        files = {"file": (filename, file_bytes)}
        data = {}
        if conversation_id:
            data["conversation_id"] = conversation_id
        response = requests.post(endpoint, files=files, data=data, timeout=60)
        response.raise_for_status()
        return response.json()

    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/conversation/{conversation_id}", timeout=10)
        response.raise_for_status()
        return response.json()

    def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            response = requests.get(f"{self.base_url}/conversation/all?limit={limit}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

    def delete_conversation(self, conversation_id: str) -> bool:
        try:
            response = requests.delete(f"{self.base_url}/conversation/{conversation_id}", timeout=10)
            return response.status_code == 200
        except Exception:
            return False


api_client = ApiClient()
