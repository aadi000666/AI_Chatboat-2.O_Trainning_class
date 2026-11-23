import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text
)
from sqlalchemy.orm import relationship
from backend.database.connection import DatabaseBase


def current_utc_time():
    return datetime.now(timezone.utc)


class ConversationModel(DatabaseBase):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=current_utc_time, nullable=False, index=True)
    updated_at = Column(DateTime, default=current_utc_time, onupdate=current_utc_time, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    messages = relationship(
        "MessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="MessageModel.created_at"
    )
    uploaded_files = relationship(
        "UploadedFileModel",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    processing_histories = relationship(
        "ProcessingHistoryModel",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


class MessageModel(DatabaseBase):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    response_type = Column(String(30), default="text", nullable=False)
    has_audio = Column(Boolean, default=False, nullable=False)
    has_image = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=current_utc_time, nullable=False, index=True)

    conversation = relationship("ConversationModel", back_populates="messages")
    uploaded_files = relationship("UploadedFileModel", back_populates="message")
    processing_history = relationship("ProcessingHistoryModel", back_populates="message", uselist=False)


class UploadedFileModel(DatabaseBase):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=current_utc_time, nullable=False)

    conversation = relationship("ConversationModel", back_populates="uploaded_files")
    message = relationship("MessageModel", back_populates="uploaded_files")
    document_metadata = relationship("DocumentMetadataModel", back_populates="uploaded_file", uselist=False, cascade="all, delete-orphan")


class DocumentMetadataModel(DatabaseBase):
    __tablename__ = "document_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String(36), ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False, index=True)
    total_chunks = Column(Integer, default=0, nullable=False)
    document_hash = Column(String(64), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    indexing_status = Column(String(30), default="pending", nullable=False)
    created_at = Column(DateTime, default=current_utc_time, nullable=False)

    uploaded_file = relationship("UploadedFileModel", back_populates="document_metadata")


class ProcessingHistoryModel(DatabaseBase):
    __tablename__ = "processing_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)
    modality = Column(String(30), nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    tokens_used = Column(Integer, default=0, nullable=False)
    rag_used = Column(Boolean, default=False, nullable=False)
    status = Column(String(30), nullable=False)
    error_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=current_utc_time, nullable=False, index=True)

    conversation = relationship("ConversationModel", back_populates="processing_histories")
    message = relationship("MessageModel", back_populates="processing_history")
