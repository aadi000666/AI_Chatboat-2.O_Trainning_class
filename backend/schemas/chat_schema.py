from typing import List, Optional
from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    document_name: str
    chunk_index: int
    excerpt: str
    similarity_score: Optional[float] = None


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=15000)
    request_audio_response: bool = False
    attached_file_ids: List[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    response_text: str
    response_type: str = "text"
    audio_output: Optional[str] = None
    image_output: Optional[str] = None
    sources: List[SourceReference] = Field(default_factory=list)
    processing_status: str = "success"
    emotional_context_detected: bool = False
