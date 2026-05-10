"""Projects router using SQLModel."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import List

from models.database import get_db, Project, Chapter
from models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse

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
