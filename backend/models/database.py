"""Database models using SQLModel with SQLite for local-first desktop app."""

from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session, select
from sqlalchemy import event
import os
import uuid

# SQLite database path - stored in user's data directory for desktop app
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audiobook.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Create engine with SQLite optimizations for local usage
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)


def get_db():
    """Get database session."""
    with Session(engine) as session:
        yield session


def create_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def generate_uuid() -> str:
    """Generate a unique UUID string."""
    return str(uuid.uuid4())


# Project Model
class Project(SQLModel, table=True):
    """Audio book project containing multiple chapters."""
    __tablename__ = "projects"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    title: str = Field(..., description="Project title")
    description: Optional[str] = Field(default=None, description="Project description")
    language: str = Field(default="en", description="Primary language code (e.g., 'en', 'ar')")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    chapters: List["Chapter"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "Chapter.order_index"}
    )


# Chapter Model
class Chapter(SQLModel, table=True):
    """Individual chapter within a project."""
    __tablename__ = "chapters"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    project_id: str = Field(..., foreign_key="projects.id", ondelete="CASCADE")
    title: str = Field(..., description="Chapter title")
    content: str = Field(..., description="Chapter text content")
    order_index: int = Field(default=0, description="Order within project")
    language: str = Field(default="en", description="Chapter language")
    voice_id: Optional[str] = Field(default=None, description="TTS voice identifier")
    audio_path: Optional[str] = Field(default=None, description="Path to generated audio file")
    duration_seconds: Optional[float] = Field(default=None, description="Audio duration in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Project = Relationship(back_populates="chapters")


# TTS Cache Model - for caching generated audio to avoid regeneration
class TTSCache(SQLModel, table=True):
    """Cache for TTS generated audio to improve performance."""
    __tablename__ = "tts_cache"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    text_hash: str = Field(..., index=True, description="Hash of the text content")
    voice_id: str = Field(..., description="Voice used for generation")
    audio_path: str = Field(..., description="Path to cached audio file")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# OCR Cache Model - for caching OCR results
class OCRCache(SQLModel, table=True):
    """Cache for OCR results to avoid re-processing."""
    __tablename__ = "ocr_cache"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    file_hash: str = Field(..., index=True, description="Hash of the source file")
    language: str = Field(..., description="OCR language used")
    extracted_text: str = Field(..., description="OCR extracted text")
    created_at: datetime = Field(default_factory=datetime.utcnow)
