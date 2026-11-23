from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.connection import get_database_session
from backend.database.crud import (
    create_conversation,
    get_conversation_by_id,
    list_active_conversations,
    hard_delete_conversation
)
from backend.schemas.conversation_schema import (
    ConversationDetailResponse,
    ConversationSummary,
    MessageSchema
)
from typing import List

conversation_router = APIRouter(prefix="/conversation", tags=["Conversations"])


@conversation_router.post("", response_model=ConversationSummary, status_code=status.HTTP_201_CREATED)
def create_new_conversation_endpoint(session: Session = Depends(get_database_session)):
    conversation = create_conversation(session=session)
    return ConversationSummary(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@conversation_router.get("/all", response_model=List[ConversationSummary])
def list_conversations_endpoint(limit: int = 50, session: Session = Depends(get_database_session)):
    conversations = list_active_conversations(session=session, limit=limit)
    return [
        ConversationSummary(
            id=item.id,
            title=item.title,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        for item in conversations
    ]


@conversation_router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_endpoint(conversation_id: str, session: Session = Depends(get_database_session)):
    conversation = get_conversation_by_id(session=session, conversation_id=conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found."
        )

    formatted_messages = [
        MessageSchema(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_role=message.sender_role,
            content=message.content,
            response_type=message.response_type,
            has_audio=message.has_audio,
            has_image=message.has_image,
            created_at=message.created_at
        )
        for message in conversation.messages
    ]

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=formatted_messages
    )


@conversation_router.delete("/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation_endpoint(conversation_id: str, session: Session = Depends(get_database_session)):
    deleted = hard_delete_conversation(session=session, conversation_id=conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found."
        )
    return {"status": "success", "message": f"Conversation {conversation_id} deleted successfully."}
