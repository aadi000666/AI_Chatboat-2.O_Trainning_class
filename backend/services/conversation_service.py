from typing import List
from sqlalchemy.orm import Session
from google.genai import types
from backend.database.crud import get_conversation_by_id, get_conversation_messages
from backend.database.models import MessageModel


class ConversationService:
    def format_history_for_gemini(
        self,
        session: Session,
        conversation_id: str,
        max_history_turns: int = 15
    ) -> List[types.Content]:
        db_messages: List[MessageModel] = get_conversation_messages(
            session=session,
            conversation_id=conversation_id,
            limit=max_history_turns
        )

        formatted_contents = []
        for message in db_messages:
            gemini_role = "user" if message.sender_role == "user" else "model"
            content_part = types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=message.content)]
            )
            formatted_contents.append(content_part)

        return formatted_contents

    def update_conversation_title_if_default(
        self,
        session: Session,
        conversation_id: str,
        user_initial_message: str
    ):
        conversation = get_conversation_by_id(session, conversation_id)
        if conversation and conversation.title in ("New Conversation", "Untitled"):
            trimmed_title = user_initial_message.strip()[:40]
            if len(user_initial_message.strip()) > 40:
                trimmed_title += "..."
            conversation.title = trimmed_title
            session.commit()


conversation_service = ConversationService()
