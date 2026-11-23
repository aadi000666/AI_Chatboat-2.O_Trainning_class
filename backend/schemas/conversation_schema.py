from datetime import datetime
from typing import List
from pydantic import BaseModel


class MessageSchema(BaseModel):
    id: str
    conversation_id: str
    sender_role: str
    content: str
    response_type: str
    has_audio: bool
    has_image: bool
    created_at: datetime


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageSchema]


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class HealthCheckResponse(BaseModel):
    status: str
    database_connected: bool
    gemini_configured: bool
    timestamp: str
