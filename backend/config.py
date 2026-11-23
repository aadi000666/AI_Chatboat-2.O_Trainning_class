from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "gemini-embedding-001"

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "multimodal_chatbot_db"

    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 8501
    BACKEND_API_BASE_URL: str = "http://127.0.0.1:8000"

    MAX_UPLOAD_SIZE_MB: int = 25
    STORAGE_UPLOAD_DIR: str = "storage/uploads"
    STORAGE_VECTOR_DIR: str = "storage/vector_index"
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    @property
    def mysql_connection_uri(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        )

    @property
    def upload_directory_path(self) -> Path:
        resolved_path = Path(self.STORAGE_UPLOAD_DIR)
        resolved_path.mkdir(parents=True, exist_ok=True)
        return resolved_path

    @property
    def vector_directory_path(self) -> Path:
        resolved_path = Path(self.STORAGE_VECTOR_DIR)
        resolved_path.mkdir(parents=True, exist_ok=True)
        return resolved_path


application_settings = ApplicationSettings()
