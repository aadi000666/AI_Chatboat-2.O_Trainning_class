from typing import Optional
from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    file_id: str
    conversation_id: str
    original_filename: str
    file_type: str
    mime_type: str
    file_size_bytes: int
    extracted_text_preview: Optional[str] = None
    chunks_created: Optional[int] = None
    status: str = "success"
