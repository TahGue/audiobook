from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChapterBase(BaseModel):
    title: str
    content: str
    language: Optional[str] = "en"
    voice_id: Optional[str] = None
    order_index: Optional[int] = 0


class ChapterCreate(ChapterBase):
    project_id: str


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    voice_id: Optional[str] = None
    order_index: Optional[int] = None
    audio_path: Optional[str] = None
    duration_seconds: Optional[float] = None


class ChapterResponse(ChapterBase):
    id: str
    project_id: str
    audio_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    language: Optional[str] = "en"
    voice_profile_id: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    voice_profile_id: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    chapters: List[ChapterResponse] = []

    model_config = {"from_attributes": True}


class ProjectListResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    chapter_count: int = 0

    model_config = {"from_attributes": True}
