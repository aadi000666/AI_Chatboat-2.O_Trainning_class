import base64
import os
import streamlit as st
from frontend.utils.api_client import api_client

st.set_page_config(
    page_title="Multimodal AI Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_file_ids" not in st.session_state:
    st.session_state.uploaded_file_ids = []
if "uploaded_file_previews" not in st.session_state:
    st.session_state.uploaded_file_previews = []
if "request_audio" not in st.session_state:
    st.session_state.request_audio = False

with st.sidebar:
    st.title("🛡️ Multimodal AI")
    st.caption("Secure RAG & Conversational Assistant")

    health_info = api_client.check_health()
    if health_info.get("status") == "healthy":
        st.success("Backend: Connected (DB Active)", icon="✅")
    elif health_info.get("status") == "database_unavailable":
        st.warning("Backend: Online (DB Pending)", icon="⚠️")
    else:
        st.error("Backend: Offline", icon="❌")

    st.divider()

    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.session_state.uploaded_file_ids = []
        st.session_state.uploaded_file_previews = []
        st.rerun()

    st.subheader("📎 Multimodal Attachments")

    image_file = st.file_uploader(
        "Image (JPG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "webp"],
        key="uploader_image"
    )
    if image_file:
        existing_names = [item["name"] for item in st.session_state.uploaded_file_previews]
        if image_file.name not in existing_names:
            with st.spinner("Uploading and verifying image..."):
                image_bytes = image_file.getvalue()
                result = api_client.upload_media(
                    file_bytes=image_bytes,
                    filename=image_file.name,
                    media_type="image",
                    conversation_id=st.session_state.conversation_id
                )
                if "file_id" in result:
                    st.session_state.uploaded_file_ids.append(result["file_id"])
                    st.session_state.uploaded_file_previews.append({
                        "name": image_file.name,
                        "type": "image",
                        "data": image_bytes
                    })
                    if not st.session_state.conversation_id:
                        st.session_state.conversation_id = result.get("conversation_id")
                    st.toast(f"Image verified & attached: {image_file.name}", icon="🖼️")

    doc_file = st.file_uploader(
        "Document for RAG (PDF, TXT, DOCX)",
        type=["pdf", "txt", "docx"],
        key="uploader_doc"
    )
    if doc_file:
        existing_names = [item["name"] for item in st.session_state.uploaded_file_previews]
        if doc_file.name not in existing_names:
            with st.spinner("Extracting & vectorizing document for RAG..."):
                doc_bytes = doc_file.getvalue()
                result = api_client.upload_media(
                    file_bytes=doc_bytes,
                    filename=doc_file.name,
                    media_type="document",
                    conversation_id=st.session_state.conversation_id
                )
                if "file_id" in result:
                    st.session_state.uploaded_file_ids.append(result["file_id"])
                    chunks = result.get("chunks_created", 0)
                    st.session_state.uploaded_file_previews.append({
                        "name": doc_file.name,
                        "type": "document",
                        "chunks": chunks
                    })
                    if not st.session_state.conversation_id:
                        st.session_state.conversation_id = result.get("conversation_id")
                    st.toast(f"Indexed {chunks} chunks from: {doc_file.name}", icon="📄")

    audio_file = st.file_uploader(
        "Audio (WAV, MP3, M4A, OGG)",
        type=["wav", "mp3", "m4a", "ogg"],
        key="uploader_audio"
    )
    if audio_file:
        existing_names = [item["name"] for item in st.session_state.uploaded_file_previews]
        if audio_file.name not in existing_names:
            with st.spinner("Uploading and analyzing audio..."):
                audio_bytes = audio_file.getvalue()
                result = api_client.upload_media(
                    file_bytes=audio_bytes,
                    filename=audio_file.name,
                    media_type="audio",
                    conversation_id=st.session_state.conversation_id
                )
                if "file_id" in result:
                    st.session_state.uploaded_file_ids.append(result["file_id"])
                    st.session_state.uploaded_file_previews.append({
                        "name": audio_file.name,
                        "type": "audio",
                        "data": audio_bytes
                    })
                    if not st.session_state.conversation_id:
                        st.session_state.conversation_id = result.get("conversation_id")
                    st.toast(f"Audio attached: {audio_file.name}", icon="🎙️")

    if st.session_state.uploaded_file_previews:
        st.divider()
        st.write("**Active File Previews:**")
        for preview in st.session_state.uploaded_file_previews:
            st.caption(f"📎 **{preview['name']}** ({preview['type']})")
            if preview["type"] == "image":
                st.image(preview["data"], width=180)
            elif preview["type"] == "audio":
                st.audio(preview["data"])
            elif preview["type"] == "document":
                st.caption(f"Indexed chunks: {preview.get('chunks', 0)}")

    st.divider()
    st.session_state.request_audio = st.toggle("Enable Voice (TTS) Responses", value=st.session_state.request_audio)

    st.divider()
    st.subheader("💬 Past Conversations")
    conversation_list = api_client.list_conversations()
    for item in conversation_list:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(item.get("title", "Untitled")[:24], key=f"conv_{item['id']}", use_container_width=True):
                detail = api_client.get_conversation(item["id"])
                st.session_state.conversation_id = item["id"]
                st.session_state.messages = [
                    {
                        "role": m["sender_role"],
                        "content": m["content"],
                        "type": m.get("response_type", "text"),
                        "has_audio": m.get("has_audio", False),
                        "has_image": m.get("has_image", False)
                    }
                    for m in detail.get("messages", [])
                ]
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{item['id']}"):
                api_client.delete_conversation(item["id"])
                if st.session_state.conversation_id == item["id"]:
                    st.session_state.conversation_id = None
                    st.session_state.messages = []
                st.rerun()

st.header("OmniMind: Multimodal AI Knowledge & Emotional Support")
st.caption("Google Gemini Multimodal • Local Vector RAG • Safe Empathetic Companion")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("audio_data"):
            audio_bytes = base64.b64decode(msg["audio_data"])
            st.audio(audio_bytes, format="audio/mp3")
        if msg.get("sources"):
            with st.expander("📚 Grounded Knowledge Citations"):
                for src in msg["sources"]:
                    st.markdown(f"**Document:** `{src.get('document_name')}` (Chunk {src.get('chunk_index')})")
                    if src.get("similarity_score") is not None:
                        st.caption(f"Similarity Score: {src.get('similarity_score')}")
                    st.caption(src.get("excerpt"))

user_prompt = st.chat_input("Ask a question, upload media, or express how you're feeling...")

if user_prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": user_prompt
    })

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing multimodal query and reasoning..."):
            try:
                response = api_client.send_chat(
                    message=user_prompt,
                    conversation_id=st.session_state.conversation_id,
                    request_audio_response=st.session_state.request_audio,
                    attached_file_ids=st.session_state.uploaded_file_ids
                )

                st.session_state.conversation_id = response.get("conversation_id")
                response_text = response.get("response_text", "")
                sources = response.get("sources", [])
                audio_output = response.get("audio_output")
                emotional_detected = response.get("emotional_context_detected", False)
                processing_status = response.get("processing_status", "success")

                if processing_status == "blocked":
                    st.warning(response_text, icon="🛡️")
                else:
                    st.markdown(response_text)

                if emotional_detected:
                    st.info("💡 Empathetic Support Mode active. Remember: OmniMind is an AI companion, not a licensed medical professional.", icon="💚")

                if audio_output:
                    audio_bytes = base64.b64decode(audio_output)
                    st.audio(audio_bytes, format="audio/mp3")

                if sources:
                    with st.expander("📚 Grounded Knowledge Citations"):
                        for src in sources:
                            st.markdown(f"**Document:** `{src.get('document_name')}` (Chunk {src.get('chunk_index')})")
                            if src.get("similarity_score") is not None:
                                st.caption(f"Similarity Score: {src.get('similarity_score')}")
                            st.caption(src.get("excerpt"))

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "audio_data": audio_output,
                    "sources": sources,
                    "type": response.get("response_type", "text")
                })

                st.session_state.uploaded_file_ids = []
                st.session_state.uploaded_file_previews = []

            except Exception as error:
                st.error(f"Error processing request: {str(error)}")
