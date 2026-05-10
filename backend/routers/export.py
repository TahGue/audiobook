from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models.database import get_db, Project, Chapter
from typing import Literal
import os
import asyncio

router = APIRouter()

AUDIO_DIR = os.getenv("AUDIO_DIR", "./audio")


class ExportRequest(BaseModel):
    format: Literal["mp3", "wav", "flac"] = "mp3"
    quality: Literal["128k", "192k", "320k"] = "192k"
    add_silence_ms: int = 1000


@router.post("/{project_id}")
async def export_project(
    project_id: str,
    data: ExportRequest,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chapters = (
        db.query(Chapter)
        .filter(Chapter.project_id == project_id, Chapter.audio_path.isnot(None))
        .order_by(Chapter.order_index)
        .all()
    )

    if not chapters:
        raise HTTPException(status_code=400, detail="No chapters with audio found")

    audio_files = [c.audio_path for c in chapters if os.path.exists(c.audio_path)]
    if not audio_files:
        raise HTTPException(status_code=400, detail="Audio files not found on disk")

    export_dir = f"{AUDIO_DIR}/{project_id}/exports"
    os.makedirs(export_dir, exist_ok=True)
    output_path = f"{export_dir}/full_book.{data.format}"

    await _merge_and_export(audio_files, output_path, data.format, data.quality, data.add_silence_ms)

    return FileResponse(
        output_path,
        media_type=_media_type(data.format),
        filename=f"{project.title}.{data.format}",
    )


async def _merge_and_export(
    files: list,
    output: str,
    fmt: str,
    quality: str,
    silence_ms: int,
):
    try:
        import ffmpeg
    except ImportError:
        raise RuntimeError("ffmpeg-python not installed")

    if len(files) == 1:
        inp = ffmpeg.input(files[0])
    else:
        inputs = [ffmpeg.input(f) for f in files]
        inp = ffmpeg.concat(*inputs, v=0, a=1)

    kwargs = {}
    if fmt == "mp3":
        kwargs = {"audio_bitrate": quality, "acodec": "libmp3lame"}
    elif fmt == "flac":
        kwargs = {"acodec": "flac"}

    stream = ffmpeg.output(inp, output, **kwargs)
    proc = ffmpeg.run_async(stream, overwrite_output=True, quiet=True)
    await asyncio.get_event_loop().run_in_executor(None, proc.wait)


def _media_type(fmt: str) -> str:
    return {"mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac"}.get(fmt, "audio/wav")
