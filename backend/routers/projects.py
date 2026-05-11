"""Projects router for project management."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional, List

from models.database import get_db, Project, Chapter
from models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from services.one_click_audiobook_service import one_click_audiobook_service, AudiobookConfig
from sqlalchemy import func

router = APIRouter()


@router.get("/", response_model=list[ProjectListResponse])
def list_projects(db: Session = Depends(get_db)):
    """List all projects with chapter counts."""
    # Get projects with chapter counts using SQLModel
    statement = select(Project).order_by(Project.created_at.desc())
    projects = db.exec(statement).all()
    
    result = []
    for project in projects:
        # Count chapters for each project
        chapter_count = db.exec(
            select(func.count(Chapter.id)).where(Chapter.project_id == project.id)
        ).one()
        
        result.append(ProjectListResponse(
            id=project.id,
            title=project.title,
            description=project.description,
            language=project.language,
            created_at=project.created_at,
            updated_at=project.updated_at,
            chapter_count=chapter_count or 0,
        ))
    return result


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    project = Project.from_orm(data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a specific project by ID."""
    statement = select(Project).where(Project.id == project_id)
    project = db.exec(statement).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, data: ProjectUpdate, db: Session = Depends(get_db)):
    """Update a project."""
    statement = select(Project).where(Project.id == project_id)
    project = db.exec(statement).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project and all its chapters (cascade)."""
    statement = select(Project).where(Project.id == project_id)
    project = db.exec(statement).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()


class OneClickAudiobookRequest(BaseModel):
    document_path: str
    voice_id: str
    language: str = "en"
    format: str = "mp3"
    quality: str = "192k"
    add_background_music: bool = False
    background_music_volume: int = 50
    auto_split_chapters: bool = True
    target_chapter_length: int = 5000


@router.post("/{project_id}/one-click")
def generate_one_click_audiobook(
    project_id: str,
    data: OneClickAudiobookRequest,
    db: Session = Depends(get_db)
):
    """Generate complete audiobook in one click."""
    # Verify project exists
    statement = select(Project).where(Project.id == project_id)
    project = db.exec(statement).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        config = AudiobookConfig(
            project_id=project_id,
            document_path=data.document_path,
            voice_id=data.voice_id,
            language=data.language,
            format=data.format,
            quality=data.quality,
            add_background_music=data.add_background_music,
            background_music_volume=data.background_music_volume,
            auto_split_chapters=data.auto_split_chapters,
            target_chapter_length=data.target_chapter_length
        )
        
        result = one_click_audiobook_service.generate_audiobook(config)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/one-click/status")
def get_one_click_status(project_id: str):
    """Get status of one-click audiobook generation."""
    # Find the job for this project
    job_id = None
    for key in one_click_audiobook_service.status:
        if key.startswith(f"audiobook_{project_id}"):
            job_id = key
            break
    
    if not job_id:
        return {"status": "not_started", "message": "No generation job found"}
    
    return one_click_audiobook_service.get_status(job_id)
