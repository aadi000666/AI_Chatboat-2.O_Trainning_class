import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from backend.config import application_settings
from backend.database.connection import get_database_session
from backend.database.crud import (
    create_conversation,
    get_conversation_by_id,
    record_uploaded_file
)
from backend.processors.audio_processor import AudioProcessorException, audio_processor
from backend.processors.image_processor import ImageProcessorException, image_processor
from backend.schemas.upload_schema import FileUploadResponse
from backend.services.rag_service import rag_service
from backend.services.security_service import SecurityException, security_service

upload_router = APIRouter(prefix="/upload", tags=["Uploads"])


@upload_router.post("/image", response_model=FileUploadResponse)
async def upload_image_endpoint(
    file: UploadFile = File(...),
    conversation_id: str = Form(None),
    session: Session = Depends(get_database_session)
):
    if conversation_id:
        conversation = get_conversation_by_id(session, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found."
            )
        active_conversation_id = conversation.id
    else:
        new_conv = create_conversation(session, title=f"Image upload: {file.filename}")
        active_conversation_id = new_conv.id

    file_bytes = await file.read()

    try:
        security_service.validate_file_size_and_path(file_bytes, file.filename or "image.png")
    except SecurityException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    if not security_service.verify_file_magic_bytes(file_bytes, "image"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match expected image signatures."
        )

    try:
        image_format, width, height = image_processor.validate_and_inspect_image(file_bytes)
    except ImageProcessorException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    sanitized_filename = security_service.sanitize_filename(file.filename or "image.png")
    stored_name = f"{uuid.uuid4()}_{sanitized_filename}"
    target_path = application_settings.upload_directory_path / stored_name

    with open(target_path, "wb") as output_stream:
        output_stream.write(file_bytes)

    detected_mime = f"image/{image_format.lower()}"
    record = record_uploaded_file(
        session=session,
        conversation_id=active_conversation_id,
        original_filename=sanitized_filename,
        stored_filename=stored_name,
        file_type="image",
        mime_type=file.content_type or detected_mime,
        file_size_bytes=len(file_bytes),
        storage_path=str(target_path)
    )

    return FileUploadResponse(
        file_id=record.id,
        conversation_id=active_conversation_id,
        original_filename=record.original_filename,
        file_type="image",
        mime_type=record.mime_type,
        file_size_bytes=record.file_size_bytes,
        status="uploaded"
    )


@upload_router.post("/document", response_model=FileUploadResponse)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    conversation_id: str = Form(None),
    session: Session = Depends(get_database_session)
):
    if conversation_id:
        conversation = get_conversation_by_id(session, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found."
            )
        active_conversation_id = conversation.id
    else:
        new_conv = create_conversation(session, title=f"Document upload: {file.filename}")
        active_conversation_id = new_conv.id

    file_bytes = await file.read()

    try:
        security_service.validate_file_size_and_path(file_bytes, file.filename or "doc.pdf")
    except SecurityException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    if not security_service.verify_file_magic_bytes(file_bytes, "document"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match expected document format signatures."
        )

    sanitized_filename = security_service.sanitize_filename(file.filename or "doc.pdf")
    stored_name = f"{uuid.uuid4()}_{sanitized_filename}"
    target_path = application_settings.upload_directory_path / stored_name

    with open(target_path, "wb") as output_stream:
        output_stream.write(file_bytes)

    record = record_uploaded_file(
        session=session,
        conversation_id=active_conversation_id,
        original_filename=sanitized_filename,
        stored_filename=stored_name,
        file_type="document",
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(file_bytes),
        storage_path=str(target_path)
    )

    ingest_result = rag_service.ingest_document(
        file_id=record.id,
        file_path=str(target_path),
        original_filename=record.original_filename,
        mime_type=record.mime_type,
        session=session
    )

    return FileUploadResponse(
        file_id=record.id,
        conversation_id=active_conversation_id,
        original_filename=record.original_filename,
        file_type="document",
        mime_type=record.mime_type,
        file_size_bytes=record.file_size_bytes,
        extracted_text_preview=ingest_result.get("text_preview"),
        chunks_created=ingest_result.get("chunks_count"),
        status="indexed"
    )


@upload_router.post("/audio", response_model=FileUploadResponse)
async def upload_audio_endpoint(
    file: UploadFile = File(...),
    conversation_id: str = Form(None),
    session: Session = Depends(get_database_session)
):
    if conversation_id:
        conversation = get_conversation_by_id(session, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found."
            )
        active_conversation_id = conversation.id
    else:
        new_conv = create_conversation(session, title=f"Audio upload: {file.filename}")
        active_conversation_id = new_conv.id

    file_bytes = await file.read()

    try:
        security_service.validate_file_size_and_path(file_bytes, file.filename or "audio.mp3")
    except SecurityException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    if not security_service.verify_file_magic_bytes(file_bytes, "audio"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match expected audio signatures."
        )

    try:
        detected_mime = audio_processor.validate_audio_file(file.filename or "", file_bytes)
    except AudioProcessorException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    sanitized_filename = security_service.sanitize_filename(file.filename or "audio.mp3")
    stored_name = f"{uuid.uuid4()}_{sanitized_filename}"
    target_path = application_settings.upload_directory_path / stored_name

    with open(target_path, "wb") as output_stream:
        output_stream.write(file_bytes)

    record = record_uploaded_file(
        session=session,
        conversation_id=active_conversation_id,
        original_filename=sanitized_filename,
        stored_filename=stored_name,
        file_type="audio",
        mime_type=file.content_type or detected_mime,
        file_size_bytes=len(file_bytes),
        storage_path=str(target_path)
    )

    return FileUploadResponse(
        file_id=record.id,
        conversation_id=active_conversation_id,
        original_filename=record.original_filename,
        file_type="audio",
        mime_type=record.mime_type,
        file_size_bytes=record.file_size_bytes,
        status="uploaded"
    )
