# OmniMind: Secure Multimodal AI Chatbot (Gemini & RAG)

A full-stack, modular, and secure Multimodal AI Chatbot powered by **Google Gemini**, **Retrieval-Augmented Generation (RAG)**, **FastAPI**, **MySQL**, and **Streamlit**.

---

## 1. Capabilities & Core Modules

1. **Multimodal Conversational AI:**
   - Text chat with persistent conversational context memory across multiple turns.
   - Image understanding (JPG, JPEG, PNG, WEBP) using Pillow verification and Gemini Multimodal.
   - Document ingestion and Q&A (PDF, TXT, DOCX).
   - Audio input comprehension (WAV, MP3, M4A, OGG).
   - Text-to-Speech (TTS) voice responses rendered directly in the Streamlit player.

2. **RAG-Based Knowledge Assistant:**
   - Document ingestion pipeline: text extraction, SHA-256 integrity hashing, recursive text chunking with overlap.
   - Vector embeddings generated using `gemini-embedding-001`.
   - Local vector store with normalized cosine similarity search ($S(u, v) = \frac{u \cdot v}{\|u\| \|v\|}$).
   - Grounded context generation with explicit source citations (document name, chunk index, similarity score).
   - Strict untrusted data boundaries protecting against indirect prompt injection.

3. **Secure Communication Portal:**
   - File validation: magic byte verification (PDF, PNG, JPEG, WEBP, DOCX, WAV, MP3, OGG), file size restrictions, and path traversal protection.
   - Prompt injection and system override pattern detection.
   - In-memory rate limiting per client IP (sliding window).
   - Parameterized SQL queries using SQLAlchemy ORM to prevent SQL injection.
   - Cascade conversation deletion purging both database records and physical file storage.

4. **Personal Emotional Support Companion:**
   - Emotion awareness detecting stress, loneliness, sadness, and frustration.
   - Validating, calm, non-judgmental conversational steering with healthy coping suggestions.
   - Strict crisis safety guardrails: immediate emergency helpline contact information (988 Lifeline, Crisis Text Line 741741, 112/911) and disclaimers clarifying that AI is not a licensed therapist or medical professional.

---

## 2. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.10+ (tested on Python 3.14) |
| Frontend | Streamlit |
| Backend Framework | FastAPI |
| Database | MySQL (SQLAlchemy ORM + PyMySQL) |
| LLM Provider | Google Gemini (`gemini-2.5-flash`) |
| Embedding Model | `gemini-embedding-001` |
| Vector Indexing | Local NumPy Cosine Similarity Vector Store |
| API Communication | REST API (Pydantic models, JSON, multipart uploads) |

---

## 3. Installation & Local Setup

### Step 1: Environment Configuration
Create a `.env` file in the project root based on `.env.example`:

```ini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=multimodal_chatbot_db

BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_PORT=8501
BACKEND_API_BASE_URL=http://127.0.0.1:8000

MAX_UPLOAD_SIZE_MB=25
STORAGE_UPLOAD_DIR=storage/uploads
STORAGE_VECTOR_DIR=storage/vector_index
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### Step 2: MySQL Database Initialization
Ensure your MySQL server is running (locally, via XAMPP, or Docker), and create the database:

```sql
CREATE DATABASE IF NOT EXISTS multimodal_chatbot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 3: Install Python Dependencies
```bash
python -m pip install -r requirements.txt
```

---

## 4. Running the Application

### Start the FastAPI Backend Server
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation will be available at:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
- **Health Check:** `http://127.0.0.1:8000/health`

### Start the Streamlit Frontend Interface
In a separate terminal:
```bash
streamlit run frontend/app.py --server.port 8501
```
The interface opens at `http://localhost:8501`.

---

## 5. Running the Automated Test Suite

Execute the full suite of 28 unit and integration tests covering API endpoints, RAG chunking and vector search, multimodal processing, security validations, and emotional safety guardrails:

```bash
python -m pytest tests/ -v
```

---

## 6. Project Architecture

```
multimodal_ai_chatbot/
│
├── frontend/
│   ├── app.py                     # Streamlit application entry point
│   └── utils/
│       └── api_client.py          # REST client communicating with FastAPI
│
├── backend/
│   ├── main.py                    # FastAPI server, rate limiting, CORS, lifespan
│   ├── config.py                  # Pydantic Settings and environment configuration
│   │
│   ├── routes/
│   │   ├── chat.py                # POST /chat endpoint
│   │   ├── upload.py              # POST /upload/image, /document, /audio
│   │   └── conversation.py        # GET & DELETE /conversation/{id}
│   │
│   ├── schemas/
│   │   ├── chat_schema.py         # Request and response Pydantic contracts
│   │   ├── upload_schema.py       # File upload schemas
│   │   └── conversation_schema.py # Conversation and health schemas
│   │
│   ├── services/
│   │   ├── ai_engine.py           # Central orchestration engine
│   │   ├── gemini_service.py      # Google GenAI client (generation & embeddings)
│   │   ├── rag_service.py         # LocalVectorStore and RAG pipeline
│   │   ├── emotional_support.py   # Empathy analysis and crisis safety guardrails
│   │   ├── security_service.py    # Injection scanner, magic bytes, rate limiter
│   │   └── conversation_service.py# Turn formatting and session history
│   │
│   ├── processors/
│   │   ├── document_processor.py  # PDF, TXT, DOCX extractor and recursive chunker
│   │   ├── image_processor.py     # Pillow image inspection and Gemini Part builder
│   │   └── audio_processor.py     # Audio validation and TTS synthesis
│   │
│   └── database/
│       ├── connection.py          # SQLAlchemy engine, session maker, base
│       ├── models.py              # MySQL ORM models
│       └── crud.py                # Parameterized database queries
│
├── storage/
│   ├── uploads/                   # Stored user uploads
│   └── vector_index/              # Persistent vector store index
│
├── tests/
│   ├── test_api.py                # API and endpoint tests
│   ├── test_gemini_conversation.py# Conversation memory and turn formatting tests
│   ├── test_rag.py                # Document chunking and vector retrieval tests
│   ├── test_multimodal.py         # Image, audio, and TTS synthesis tests
│   ├── test_security.py           # Magic bytes, path traversal, injection tests
│   └── test_emotional.py          # Empathy and crisis safety guardrail tests
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```
