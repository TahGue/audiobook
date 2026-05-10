"""Chapters router using SQLModel."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from pydantic import BaseModel

from models.database import get_db, Chapter, Project
from models.schemas import ChapterCreate, ChapterUpdate, ChapterResponse
from services.arabic_text_service import arabic_service
from services.chapter_split_service import chapter_split_service

router = APIRouter()


@router.post("/", response_model=ChapterResponse, status_code=201)
def create_chapter(data: ChapterCreate, db: Session = Depends(get_db)):
    """Create a new chapter in a project."""
    # Verify project exists
    project = db.exec(select(Project).where(Project.id == data.project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get max order index for auto-increment
    max_order = db.exec(
        select(func.count(Chapter.id)).where(Chapter.project_id == data.project_id)
    ).one()
    
    # Create chapter with auto-generated ID and order
    chapter_data = data.model_dump()
    chapter_data["content"] = arabic_service.clean_arabic_text(chapter_data["content"]).text
    chapter_data["order_index"] = max_order or 0
    
    chapter = Chapter(**chapter_data)
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.get("/", response_model=list[ChapterResponse])
def list_chapters(
    project_id: str = Query(..., description="Filter by project ID"),
    db: Session = Depends(get_db)
):
    """List chapters for a project."""
    statement = select(Chapter).where(Chapter.project_id == project_id).order_by(Chapter.order_index)
    chapters = db.exec(statement).all()
    return chapters


@router.get("/{chapter_id}", response_model=ChapterResponse)
def get_chapter(chapter_id: str, db: Session = Depends(get_db)):
    """Get a specific chapter by ID."""
    statement = select(Chapter).where(Chapter.id == chapter_id)
    chapter = db.exec(statement).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.patch("/{chapter_id}", response_model=ChapterResponse)
def update_chapter(chapter_id: str, data: ChapterUpdate, db: Session = Depends(get_db)):
    """Update a chapter."""
    statement = select(Chapter).where(Chapter.id == chapter_id)
    chapter = db.exec(statement).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    if "content" in update_data and update_data["content"] is not None:
        update_data["content"] = arabic_service.clean_arabic_text(update_data["content"]).text
    for key, value in update_data.items():
        setattr(chapter, key, value)
    
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.delete("/{chapter_id}", status_code=204)
def delete_chapter(chapter_id: str, db: Session = Depends(get_db)):
    """Delete a chapter."""
    statement = select(Chapter).where(Chapter.id == chapter_id)
    chapter = db.exec(statement).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    db.delete(chapter)
    db.commit()


@router.patch("/{chapter_id}/reorder")
def reorder_chapter(chapter_id: str, order_index: int, db: Session = Depends(get_db)):
    """Reorder a chapter within a project."""
    statement = select(Chapter).where(Chapter.id == chapter_id)
    chapter = db.exec(statement).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    chapter.order_index = order_index
    db.add(chapter)
    db.commit()
    return {"success": True}


class AutoSplitRequest(BaseModel):
    text: str
    project_id: str
    language: str = "en"
    target_length: int = 5000


@router.post("/auto-split")
def auto_split_chapters(data: AutoSplitRequest, db: Session = Depends(get_db)):
    """
    Automatically split text into chapters and create them in the project.
    """
    # Verify project exists
    project = db.exec(select(Project).where(Project.id == data.project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Split text into chapters
    chapter_split_service.target_chapter_length = data.target_length
    splits = chapter_split_service.split_text(data.text, data.language)
    
    # Get current max order index
    max_order = db.exec(
        select(func.count(Chapter.id)).where(Chapter.project_id == data.project_id)
    ).one() or 0
    
    # Create chapters from splits
    created_chapters = []
    for i, split in enumerate(splits):
        chapter_data = ChapterCreate(
            title=split.title,
            content=split.content,
            project_id=data.project_id,
            language=data.language
        )
        chapter_data_dict = chapter_data.model_dump()
        chapter_data_dict["content"] = arabic_service.clean_arabic_text(chapter_data_dict["content"]).text
        chapter_data_dict["order_index"] = max_order + i
        
        chapter = Chapter(**chapter_data_dict)
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        created_chapters.append(chapter)
    
    return {
        "chapters_created": len(created_chapters),
        "chapters": created_chapters
    }
