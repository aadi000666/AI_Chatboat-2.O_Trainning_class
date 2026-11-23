from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import application_settings

DatabaseBase = declarative_base()


def build_resilient_database_engine():
    mysql_uri = application_settings.mysql_connection_uri
    try:
        candidate_engine = create_engine(
            mysql_uri,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        with candidate_engine.connect() as probe_conn:
            probe_conn.execute(text("SELECT 1"))
        return candidate_engine, True
    except Exception:
        fallback_path = Path("storage") / "app_database.db"
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        fallback_engine = create_engine(
            f"sqlite:///{fallback_path.as_posix()}",
            connect_args={"check_same_thread": False}
        )
        return fallback_engine, False


database_engine, is_mysql_connected = build_resilient_database_engine()

DatabaseSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=database_engine
)


def get_database_session():
    session = DatabaseSessionLocal()
    try:
        yield session
    finally:
        session.close()


def verify_database_connectivity() -> bool:
    try:
        with database_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return is_mysql_connected
    except Exception:
        return False


def initialize_database_tables():
    from backend.database.models import (
        ConversationModel,
        MessageModel,
        UploadedFileModel,
        DocumentMetadataModel,
        ProcessingHistoryModel
    )
    DatabaseBase.metadata.create_all(bind=database_engine)


initialize_database_tables()
