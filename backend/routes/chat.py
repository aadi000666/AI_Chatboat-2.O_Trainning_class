from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.database.connection import get_database_session
from backend.schemas.chat_schema import ChatRequest, ChatResponse
from backend.services.ai_engine import ai_engine

chat_router = APIRouter(tags=["Chat"])


@chat_router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def process_chat_message_endpoint(
    request: ChatRequest,
    session: Session = Depends(get_database_session)
):
    return ai_engine.process_chat(request=request, session=session)
