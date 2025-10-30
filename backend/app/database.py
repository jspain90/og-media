from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./og_media.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for FastAPI routes to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    _ensure_column("channels", "play_order", "TEXT NOT NULL DEFAULT 'random'")
    _ensure_column("video_queue", "published_at", "DATETIME")

def _ensure_column(table: str, column: str, definition: str):
    """Add missing columns when new fields are introduced"""
    inspector = inspect(engine)
    try:
        columns = {col["name"] for col in inspector.get_columns(table)}
    except Exception as exc:
        print(f"Failed to inspect table {table}: {exc}")
        return

    if column in columns:
        return

    ddl = f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
    with engine.connect() as connection:
        connection.execute(text(ddl))
        connection.commit()
        print(f"Added column '{column}' to '{table}'")
