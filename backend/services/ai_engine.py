import time
from pathlib import Path
from typing import List, Optional
from google.genai import types
from sqlalchemy.orm import Session
from backend.database.crud import (
    create_conversation,
    create_message,
    get_conversation_by_id,
    record_processing_history
)
from backend.database.models import UploadedFileModel
from backend.processors.audio_processor import audio_processor
from backend.processors.image_processor import image_processor
from backend.schemas.chat_schema import ChatRequest, ChatResponse, SourceReference
from backend.services.conversation_service import conversation_service
from backend.services.emotional_support import emotional_support_service
from backend.services.gemini_service import GeminiServiceException, gemini_service
from backend.services.rag_service import rag_service
from backend.services.security_service import security_service


class ConversationalAiEngine:
    def __init__(self):
        self.base_system_instruction = (
            "You are a Secure Multimodal AI Assistant. "
            "You can analyze images, listen to and transcribe audio, answer questions based on documents, and engage in helpful conversations. "
            "You provide accurate, helpful, respectful, and well-structured answers. "
            "Maintain context across conversational turns."
        )

    def process_chat(self, request: ChatRequest, session: Session) -> ChatResponse:
        start_time = time.time()
        clean_user_message = security_service.sanitize_user_input(request.message)

        if request.conversation_id:
            conversation = get_conversation_by_id(session, request.conversation_id)
            if not conversation:
                conversation = create_conversation(session, title="New Conversation")
            active_conversation_id = conversation.id
        else:
            conversation = create_conversation(session, title="New Conversation")
            active_conversation_id = conversation.id

        conversation_service.update_conversation_title_if_default(
            session=session,
            conversation_id=active_conversation_id,
            user_initial_message=clean_user_message
        )

        is_injection, injection_warning = security_service.scan_for_prompt_injection(clean_user_message)
        if is_injection:
            blocked_response_text = (
                "Security Alert: Your input triggered a security filter and cannot be processed as requested. "
                "Please reformulate your prompt without system-override or instruction-bypass directives."
            )
            user_msg = create_message(
                session=session,
                conversation_id=active_conversation_id,
                sender_role="user",
                content=clean_user_message,
                response_type="text"
            )
            asst_msg = create_message(
                session=session,
                conversation_id=active_conversation_id,
                sender_role="assistant",
                content=blocked_response_text,
                response_type="text"
            )
            record_processing_history(
                session=session,
                conversation_id=active_conversation_id,
                message_id=asst_msg.id,
                modality="text",
                processing_time_ms=int((time.time() - start_time) * 1000),
                status="blocked",
                error_details=injection_warning
            )
            return ChatResponse(
                conversation_id=active_conversation_id,
                message_id=asst_msg.id,
                response_text=blocked_response_text,
                response_type="text",
                sources=[],
                processing_status="blocked",
                emotional_context_detected=False
            )

        emotional_analysis = emotional_support_service.analyze_emotional_context(clean_user_message)
        if emotional_analysis.is_crisis:
            crisis_text = emotional_analysis.crisis_response or ""
            user_msg = create_message(
                session=session,
                conversation_id=active_conversation_id,
                sender_role="user",
                content=clean_user_message,
                response_type="text"
            )
            asst_msg = create_message(
                session=session,
                conversation_id=active_conversation_id,
                sender_role="assistant",
                content=crisis_text,
                response_type="text"
            )
            record_processing_history(
                session=session,
                conversation_id=active_conversation_id,
                message_id=asst_msg.id,
                modality="text",
                processing_time_ms=int((time.time() - start_time) * 1000),
                status="success"
            )
            return ChatResponse(
                conversation_id=active_conversation_id,
                message_id=asst_msg.id,
                response_text=crisis_text,
                response_type="text",
                sources=[],
                processing_status="success",
                emotional_context_detected=True
            )

        history_contents: List[types.Content] = conversation_service.format_history_for_gemini(
            session=session,
            conversation_id=active_conversation_id,
            max_history_turns=12
        )

        retrieved_sources: List[SourceReference] = rag_service.retrieve_relevant_context(
            query=clean_user_message,
            top_k=3
        )

        rag_used = len(retrieved_sources) > 0
        response_type = "rag_grounded" if rag_used else "text"

        instruction_parts = [self.base_system_instruction]
        if emotional_analysis.is_emotional_context:
            instruction_parts.append(emotional_analysis.support_system_instruction)

        if rag_used:
            grounded_addon = rag_service.build_grounded_system_context(retrieved_sources)
            instruction_parts.append(grounded_addon)

        effective_system_instruction = "\n".join(instruction_parts)

        turn_parts: List[types.Part] = [types.Part.from_text(text=clean_user_message)]
        has_attached_image = False
        has_attached_audio = False

        if request.attached_file_ids:
            attached_records = (
                session.query(UploadedFileModel)
                .filter(UploadedFileModel.id.in_(request.attached_file_ids))
                .all()
            )
            for record in attached_records:
                target_path = Path(record.storage_path)
                if not target_path.exists():
                    continue

                if record.file_type == "image":
                    part = image_processor.build_gemini_image_part(
                        file_path=target_path,
                        mime_type=record.mime_type
                    )
                    turn_parts.append(part)
                    has_attached_image = True

                elif record.file_type == "audio":
                    part = audio_processor.build_gemini_audio_part(
                        file_path=target_path,
                        mime_type=record.mime_type
                    )
                    turn_parts.append(part)
                    has_attached_audio = True

        current_turn = types.Content(
            role="user",
            parts=turn_parts
        )
        full_contents = history_contents + [current_turn]

        user_db_message = create_message(
            session=session,
            conversation_id=active_conversation_id,
            sender_role="user",
            content=clean_user_message,
            response_type="text",
            has_image=has_attached_image,
            has_audio=has_attached_audio
        )

        try:
            generated_text = gemini_service.generate_chat_response(
                contents=full_contents,
                system_instruction=effective_system_instruction
            )
            processing_status = "success"
            error_details = None
        except GeminiServiceException as error:
            generated_text = f"Gemini Error: {str(error)}"
            processing_status = "failed"
            error_details = str(error)

        audio_output_base64 = None
        assistant_has_audio = False
        if request.request_audio_response and processing_status == "success":
            try:
                audio_output_base64 = audio_processor.synthesize_speech_to_base64(generated_text)
                assistant_has_audio = bool(audio_output_base64)
            except Exception:
                audio_output_base64 = None

        if has_attached_image or has_attached_audio:
            response_type = "multimodal"
        elif assistant_has_audio:
            response_type = "audio"

        assistant_db_message = create_message(
            session=session,
            conversation_id=active_conversation_id,
            sender_role="assistant",
            content=generated_text,
            response_type=response_type,
            has_audio=assistant_has_audio
        )

        modality = "multimodal" if (has_attached_image and has_attached_audio) else (
            "image" if has_attached_image else (
                "audio" if (has_attached_audio or assistant_has_audio) else "text"
            )
        )

        processing_duration_ms = int((time.time() - start_time) * 1000)

        record_processing_history(
            session=session,
            conversation_id=active_conversation_id,
            message_id=assistant_db_message.id,
            modality=modality,
            processing_time_ms=processing_duration_ms,
            tokens_used=0,
            rag_used=rag_used,
            status=processing_status,
            error_details=error_details
        )

        return ChatResponse(
            conversation_id=active_conversation_id,
            message_id=assistant_db_message.id,
            response_text=generated_text,
            response_type=response_type,
            audio_output=audio_output_base64,
            sources=retrieved_sources,
            processing_status=processing_status,
            emotional_context_detected=emotional_analysis.is_emotional_context
        )


ai_engine = ConversationalAiEngine()
