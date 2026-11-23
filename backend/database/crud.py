from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import (
    ConversationModel,
    MessageModel,
    UploadedFileModel,
    DocumentMetadataModel,
    ProcessingHistoryModel
)


def create_conversation(session: Session, title: str = "New Conversation") -> ConversationModel:
    conversation = ConversationModel(title=title)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def get_conversation_by_id(session: Session, conversation_id: str) -> Optional[ConversationModel]:
    return (
        session.query(ConversationModel)
        .filter(ConversationModel.id == conversation_id, ConversationModel.is_deleted.is_(False))
        .first()
    )


def list_active_conversations(session: Session, limit: int = 50) -> List[ConversationModel]:
    return (
        session.query(ConversationModel)
        .filter(ConversationModel.is_deleted.is_(False))
        .order_by(ConversationModel.updated_at.desc())
        .limit(limit)
        .all()
    )


def soft_delete_conversation(session: Session, conversation_id: str) -> bool:
    conversation = get_conversation_by_id(session, conversation_id)
    if not conversation:
        return False
    conversation.is_deleted = True
    session.commit()
    return True


def hard_delete_conversation(session: Session, conversation_id: str) -> bool:
    conversation = (
        session.query(ConversationModel)
        .filter(ConversationModel.id == conversation_id)
        .first()
    )
    if not conversation:
        return False
    session.delete(conversation)
    session.commit()
    return True


def create_message(
    session: Session,
    conversation_id: str,
    sender_role: str,
    content: str,
    response_type: str = "text",
    has_audio: bool = False,
    has_image: bool = False
) -> MessageModel:
    message = MessageModel(
        conversation_id=conversation_id,
        sender_role=sender_role,
        content=content,
        response_type=response_type,
        has_audio=has_audio,
        has_image=has_image
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def get_conversation_messages(session: Session, conversation_id: str, limit: int = 100) -> List[MessageModel]:
    return (
        session.query(MessageModel)
        .filter(MessageModel.conversation_id == conversation_id)
        .order_by(MessageModel.created_at.asc())
        .limit(limit)
        .all()
    )


def record_uploaded_file(
    session: Session,
    conversation_id: str,
    original_filename: str,
    stored_filename: str,
    file_type: str,
    mime_type: str,
    file_size_bytes: int,
    storage_path: str,
    message_id: Optional[str] = None
) -> UploadedFileModel:
    file_record = UploadedFileModel(
        conversation_id=conversation_id,
        message_id=message_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file_type,
        mime_type=mime_type,
        file_size_bytes=file_size_bytes,
        storage_path=storage_path
    )
    session.add(file_record)
    session.commit()
    session.refresh(file_record)
    return file_record


def get_uploaded_files_by_conversation(session: Session, conversation_id: str) -> List[UploadedFileModel]:
    return (
        session.query(UploadedFileModel)
        .filter(UploadedFileModel.conversation_id == conversation_id)
        .all()
    )


def record_document_metadata(
    session: Session,
    file_id: str,
    document_hash: str,
    total_chunks: int,
    summary: Optional[str] = None,
    indexing_status: str = "indexed"
) -> DocumentMetadataModel:
    doc_meta = DocumentMetadataModel(
        file_id=file_id,
        document_hash=document_hash,
        total_chunks=total_chunks,
        summary=summary,
        indexing_status=indexing_status
    )
    session.add(doc_meta)
    session.commit()
    session.refresh(doc_meta)
    return doc_meta


def record_processing_history(
    session: Session,
    conversation_id: str,
    modality: str,
    processing_time_ms: int,
    status: str,
    message_id: Optional[str] = None,
    tokens_used: int = 0,
    rag_used: bool = False,
    error_details: Optional[str] = None
) -> ProcessingHistoryModel:
    history = ProcessingHistoryModel(
        conversation_id=conversation_id,
        message_id=message_id,
        modality=modality,
        processing_time_ms=processing_time_ms,
        tokens_used=tokens_used,
        rag_used=rag_used,
        status=status,
        error_details=error_details
    )
    session.add(history)
    session.commit()
    session.refresh(history)
    return history
