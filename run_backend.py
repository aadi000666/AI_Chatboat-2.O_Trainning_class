import uvicorn
from backend.config import application_settings

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=application_settings.BACKEND_HOST,
        port=application_settings.BACKEND_PORT,
        reload=True
    )
