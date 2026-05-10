from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models.database import get_db, Chapter
import os
import uuid
import asyncio

router = APIRouter()

AUDIO_DIR = os.getenv("AUDIO_DIR", "./audio")

VOICES = {
    "en": [
        {"id": "en_US-lessac-high", "name": "Lessac (US English)", "gender": "female"},
        {"id": "en_US-ryan-high", "name": "Ryan (US English)", "gender": "male"},
    ],
    "ar": [
        {"id": "ar_JO-kareem-medium", "name": "Kareem (Arabic)", "gender": "male"},
    ],
    "fr": [
        {"id": "fr_FR-upmc-medium", "name": "UPMC (French)", "gender": "male"},
    ],
    "es": [
        {"id": "es_ES-davefx-medium", "name": "DaveFX (Spanish)", "gender": "male"},
    ],
    "de": [
        {"id": "de_DE-thorsten-high", "name": "Thorsten (German)", "gender": "male"},
    ],
    "hi": [
        {"id": "hi_IN-anup-medium", "name": "Anup (Hindi)", "gender": "male"},
    ],
    "zh": [
        {"id": "zh_CN-huayan-medium", "name": "Huayan (Chinese)", "gender": "female"},
    ],
    "ru": [
        {"id": "ru_RU-irina-medium", "name": "Irina (Russian)", "gender": "female"},
    ],
    "pt": [
        {"id": "pt_BR-faber-medium", "name": "Faber (Portuguese)", "gender": "male"},
    ],
    "ja": [
        {"id": "ja_JP-kokoro-medium", "name": "Kokoro (Japanese)", "gender": "female"},
    ],
}

LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "ar", "name": "Arabic"},
    {"code": "fr", "name": "French"},
    {"code": "es", "name": "Spanish"},
    {"code": "de", "name": "German"},
    {"code": "hi", "name": "Hindi"},
    {"code": "zh", "name": "Mandarin Chinese"},
    {"code": "ru", "name": "Russian"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "ja", "name": "Japanese"},
]


class TTSGenerateRequest(BaseModel):
    chapter_id: str
    voice_id: str
    language: str = "en"


@router.get("/languages")
def get_languages():
    return LANGUAGES


@router.get("/voices")
def get_voices(language: str = "en"):
    return VOICES.get(language, VOICES["en"])


@router.post("/generate")
async def generate_tts(data: TTSGenerateRequest, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(Chapter.id == data.chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    os.makedirs(f"{AUDIO_DIR}/{chapter.project_id}", exist_ok=True)
    output_path = f"{AUDIO_DIR}/{chapter.project_id}/{chapter.id}.wav"

    try:
        await _run_piper(chapter.content, data.voice_id, output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

    duration = _get_duration(output_path)
    chapter.audio_path = output_path
    chapter.voice_id = data.voice_id
    chapter.language = data.language
    chapter.duration_seconds = duration
    db.commit()

    return {
        "audio_path": output_path,
        "audio_url": f"/audio/{chapter.project_id}/{chapter.id}.wav",
        "duration_seconds": duration,
    }


@router.get("/audio/{project_id}/{chapter_id}")
def serve_audio(project_id: str, chapter_id: str):
    path = f"{AUDIO_DIR}/{project_id}/{chapter_id}.wav"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path, media_type="audio/wav")


async def _run_piper(text: str, voice_id: str, output_path: str):
    models_dir = os.getenv("PIPER_MODELS_DIR", "./piper_models")
    model_path = f"{models_dir}/{voice_id}.onnx"

    if not os.path.exists(model_path):
        raise RuntimeError(
            f"Piper model not found: {model_path}. "
            f"Download from https://huggingface.co/rhasspy/piper-voices"
        )

    proc = await asyncio.create_subprocess_exec(
        "piper",
        "--model", model_path,
        "--output_file", output_path,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate(input=text.encode("utf-8"))

    if proc.returncode != 0:
        raise RuntimeError(f"Piper failed: {stderr.decode()}")


def _get_duration(path: str) -> float:
    try:
        import wave
        with wave.open(path, "rb") as f:
            frames = f.getnframes()
            rate = f.getframerate()
            return frames / float(rate)
    except Exception:
        return 0.0
