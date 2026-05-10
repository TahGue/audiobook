# Audiobook Maker — Full Project Plan

## Stack: Python FastAPI + Tauri + React

### Why This Stack
- **Python FastAPI**: Best ecosystem for AI/ML, TTS, OCR, no body size limits, async, GPU support
- **Tauri (Rust shell)**: True native desktop app, no Electron bloat, bundles Python as sidecar, native file dialogs
- **React + TailwindCSS**: Modern UI, reuse existing components, fast iteration

---

## Project Structure

```
audiobook-maker/
├── backend/                    # Python FastAPI
│   ├── main.py                 # FastAPI app entry point
│   ├── routers/
│   │   ├── projects.py         # CRUD for audiobook projects
│   │   ├── chapters.py         # CRUD for chapters
│   │   ├── tts.py              # Text-to-speech endpoints
│   │   ├── pdf.py              # PDF/OCR extraction
│   │   └── export.py           # Audio export (MP3/WAV/FLAC)
│   ├── models/
│   │   ├── database.py         # SQLAlchemy models
│   │   └── schemas.py          # Pydantic schemas
│   ├── services/
│   │   ├── tts_service.py      # Piper TTS / Coqui TTS
│   │   ├── ocr_service.py      # EasyOCR / Tesseract
│   │   ├── pdf_service.py      # pdfplumber extraction
│   │   └── audio_service.py    # FFmpeg mixing/export
│   ├── requirements.txt
│   └── alembic/                # DB migrations
│       └── versions/
├── frontend/                   # React + Vite + TailwindCSS
│   ├── src/
│   │   ├── components/
│   │   │   ├── projects/       # Project list/create/delete
│   │   │   ├── chapters/       # Chapter management
│   │   │   ├── tts/            # TTS controls
│   │   │   ├── pdf/            # PDF upload
│   │   │   └── export/         # Audio export
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── ProjectDetail.tsx
│   │   │   └── Settings.tsx
│   │   ├── lib/
│   │   │   └── api.ts          # API client (axios)
│   │   └── types/
│   │       └── audiobook.ts
│   ├── package.json
│   └── vite.config.ts
├── src-tauri/                  # Tauri Rust shell
│   ├── src/
│   │   ├── main.rs             # Tauri app entry + Python sidecar
│   │   └── commands.rs         # Tauri commands (file dialog, etc.)
│   ├── Cargo.toml
│   └── tauri.conf.json
├── PLAN.md                     # This file
└── CHECKLIST.md                # Implementation checklist
```

---

## Phases

### Phase 1 — Python FastAPI Backend
Replace Next.js API routes with FastAPI. No size limits, full Python ecosystem.

**Core stack:**
- `FastAPI` — async web framework
- `SQLAlchemy` + `alembic` — ORM + migrations
- `PostgreSQL` (Docker) — same DB
- `pdfplumber` — better PDF text extraction (especially Arabic/RTL)
- `pydantic v2` — schema validation

**TTS stack:**
- `piper-tts` — fast, offline, 10+ languages, high quality WAV
- Languages: Arabic, English, French, Spanish, German, Hindi, Chinese, Russian, Portuguese, Japanese
- Fallback: `edge-tts` (Microsoft neural voices, free, local CLI)

**OCR stack:**
- `easyocr` — Arabic, Chinese, Japanese, Hindi, 80+ languages
- `pytesseract` — fallback for simpler docs
- GPU acceleration via PyTorch CUDA (optional)

**Audio stack:**
- `ffmpeg-python` — convert WAV to MP3/FLAC, mix background music
- `pydub` — simple audio operations

### Phase 2 — React + Vite Frontend
Replace Next.js frontend with Vite + React. Faster dev, no SSR overhead.

**Features:**
- Project & chapter management
- Language + voice selection per chapter
- PDF upload with OCR toggle
- Real-time TTS generation progress
- Audio player with waveform
- Export controls (MP3/WAV/FLAC)
- Dark mode

### Phase 3 — Tauri Desktop App
Wrap everything in a native Tauri desktop app.

**Features:**
- Python FastAPI runs as Tauri sidecar (bundled)
- Native file picker (open PDF directly from disk)
- No browser needed, no ports to manage
- Auto-start backend on app launch
- System tray support
- Cross-platform (Mac/Windows/Linux)

### Phase 4 — Advanced Features
- **Voice cloning** with XTTS v2 (clone any voice from 3s sample)
- **Batch processing** — convert entire book in background
- **Chapter auto-split** by heading/page number detection
- **Background music** mixing with volume control
- **EPUB/DOCX** support
- **Bookmarks** — resume playback position
- **Speed/pitch** control in player
- **GPU acceleration** — auto-detect CUDA/Metal

---

## Database Schema

```sql
-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Chapters
CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,          -- No size limit (PostgreSQL TEXT)
    order_index INTEGER DEFAULT 0,
    language VARCHAR(10) DEFAULT 'en',
    voice_id TEXT,                  -- Piper voice model name
    audio_path TEXT,                -- Path to generated WAV file
    duration_seconds FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Audio files stored on disk (not in DB) for no size limits
-- Path: ./audio/{project_id}/{chapter_id}.wav
```

---

## API Endpoints

```
GET    /api/projects              # List all projects
POST   /api/projects              # Create project
GET    /api/projects/{id}         # Get project + chapters
DELETE /api/projects/{id}         # Delete project

GET    /api/chapters/{id}         # Get chapter
POST   /api/chapters              # Create chapter
PATCH  /api/chapters/{id}         # Update chapter
DELETE /api/chapters/{id}         # Delete chapter
PATCH  /api/chapters/{id}/reorder # Change chapter order

POST   /api/tts/generate          # Generate audio for chapter
GET    /api/tts/voices            # List available voices per language
GET    /api/tts/languages         # List supported languages
GET    /api/audio/{chapter_id}    # Stream audio file

POST   /api/pdf/extract           # Extract text from PDF (text-based)
POST   /api/pdf/ocr               # Extract text via OCR (scanned PDF)

POST   /api/export/{project_id}   # Export full book as MP3/WAV/FLAC
GET    /api/export/status/{job_id}# Check export job status
```

---

## TTS Voices Plan (Piper)

| Language | Voice Model | Quality |
|---|---|---|
| English | en_US-lessac-high | ⭐⭐⭐⭐⭐ |
| Arabic | ar_JO-kareem-medium | ⭐⭐⭐⭐ |
| French | fr_FR-upmc-medium | ⭐⭐⭐⭐ |
| Spanish | es_ES-davefx-medium | ⭐⭐⭐⭐ |
| German | de_DE-thorsten-high | ⭐⭐⭐⭐⭐ |
| Hindi | hi_IN-anup-medium | ⭐⭐⭐⭐ |
| Chinese | zh_CN-huayan-medium | ⭐⭐⭐⭐ |
| Russian | ru_RU-irina-medium | ⭐⭐⭐⭐ |
| Portuguese | pt_BR-faber-medium | ⭐⭐⭐⭐ |
| Japanese | ja_JP-kokoro-medium | ⭐⭐⭐⭐ |

---

## Key Advantages Over Next.js Version

| Feature | Next.js (old) | FastAPI + Tauri (new) |
|---|---|---|
| Body size limit | 4MB (painful) | Unlimited |
| TTS quality | Browser WASM (poor) | Piper neural (excellent) |
| Arabic PDF | Broken | pdfplumber + EasyOCR |
| Audio storage | Base64 in DB (bad) | Files on disk |
| GPU TTS | No | Yes (CUDA/Metal) |
| Voice cloning | No | Yes (XTTS v2) |
| Offline | Partial | Full |
| Native file open | No | Yes (Tauri) |
| Background jobs | No | Yes (asyncio) |
| Export MP3 | No | Yes (FFmpeg) |
