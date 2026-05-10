from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal, Optional

from models.database import get_db, Project, Chapter
from services.background_music_service import background_music_service

router = APIRouter()

AUDIO_DIR = os.getenv("AUDIO_DIR", "./audio")


class ExportRequest(BaseModel):
    format: Literal["mp3", "wav", "flac"] = "mp3"
    quality: Literal["128k", "192k", "320k"] = "192k"
    add_silence_ms: int = 1000


class BackgroundMusicConfig(BaseModel):
    music_path: str
    voice_path: str
    output_path: str
    volume: int = 50
    fade_in_duration: float = 2.0
    fade_out_duration: float = 2.0


@router.post("/background-music/upload")
async def upload_background_music(file: UploadFile = File(...)):
    """Upload a background music track."""
    try:
        # Save the uploaded file
        file_path = background_music_service.save_music_track(
            await file.read(),
            file.filename or "music.mp3"
        )
        return {"message": "Background music uploaded successfully", "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/background-music/tracks")
def list_background_music():
    """List all available background music tracks."""
    try:
        tracks = background_music_service.list_music_tracks()
        return {"tracks": tracks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/background-music/tracks/{filename}")
def delete_background_music(filename: str):
    """Delete a background music track."""
    try:
        success = background_music_service.delete_music_track(filename)
        if not success:
            raise HTTPException(status_code=404, detail="Track not found")
        return {"message": "Track deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/background-music/mix")
def mix_background_music(config: BackgroundMusicConfig):
    """Mix background music with voice audio."""
    try:
        bg_config = BackgroundMusicConfig(
            music_path=config.music_path,
            voice_path=config.voice_path,
            output_path=config.output_path,
            volume=config.volume,
            fade_in_duration=config.fade_in_duration,
            fade_out_duration=config.fade_out_duration
        )
        output_path = background_music_service.mix_audio(bg_config)
        return {"message": "Audio mixed successfully", "output_path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/background-music/preview")
def preview_background_music(config: BackgroundMusicConfig):
    """Create a preview of the mixed audio."""
    try:
        bg_config = BackgroundMusicConfig(
            music_path=config.music_path,
            voice_path=config.voice_path,
            output_path=config.output_path,
            volume=config.volume,
            fade_in_duration=config.fade_in_duration,
            fade_out_duration=config.fade_out_duration
        )
        preview_path = background_music_service.preview_mix(bg_config)
        return {"message": "Preview generated successfully", "preview_path": preview_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
