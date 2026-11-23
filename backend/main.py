from contextlib import asynccontextmanager
from datetime import datetime, timezone
# pyrefly: ignore[missing-import]
from fastapi import FastAPI, Request, status
# pyrefly: ignore[missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore[missing-import]
from fastapi.responses import JSONResponse
# pyrefly: ignore[missing-import]
import uvicorn
from backend.config import application_settings
from backend.database.connection import (
    initialize_database_tables,
    verify_database_connectivity
)
from backend.routes.chat import chat_router
from backend.routes.conversation import conversation_router
from backend.routes.upload import upload_router
from backend.schemas.conversation_schema import HealthCheckResponse
from backend.services.security_service import security_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    application_settings.upload_directory_path
    application_settings.vector_directory_path
    initialize_database_tables()
    yield


app = FastAPI(
    title="Secure Multimodal AI Chatbot API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    is_allowed = security_service.check_rate_limit(client_ip)
    if not is_allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please wait before sending more requests."}
        )
    return await call_next(request)


app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(conversation_router)


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
def health_check():
    db_ok = verify_database_connectivity()
    gemini_ok = bool(application_settings.GEMINI_API_KEY)
    status_text = "healthy" if db_ok else "database_unavailable"
    return HealthCheckResponse(
        status=status_text,
        database_connected=db_ok,
        gemini_configured=gemini_ok,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@app.get("/", tags=["Root"])
def root_status():
    return {
        "service": "Secure Multimodal AI Chatbot API",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=application_settings.BACKEND_HOST,
        port=application_settings.BACKEND_PORT,
        reload=True
    )
