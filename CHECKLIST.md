# Audiobook Maker — Implementation Checklist

## Phase 1 — Python FastAPI Backend

### Environment Setup
- [ ] Install Python 3.11+
- [ ] Create virtualenv: `python -m venv .venv`
- [ ] Install base deps: `pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary pydantic python-dotenv`
- [ ] Docker PostgreSQL running (`docker compose up -d`)
- [ ] Create `.env` with `DATABASE_URL`

### Database
- [ ] Create `backend/models/database.py` — SQLAlchemy models (Project, Chapter)
- [ ] Create `backend/models/schemas.py` — Pydantic request/response schemas
- [ ] Init Alembic: `alembic init alembic`
- [ ] Write initial migration
- [ ] Run migration: `alembic upgrade head`

### API Routes
- [ ] `backend/routers/projects.py` — GET/POST/DELETE projects
- [ ] `backend/routers/chapters.py` — GET/POST/PATCH/DELETE chapters
- [ ] `backend/routers/tts.py` — POST generate, GET voices, GET languages
- [ ] `backend/routers/pdf.py` — POST extract (text), POST ocr (scanned)
- [ ] `backend/routers/export.py` — POST export full book
- [ ] `backend/main.py` — wire all routers + CORS

### PDF Service
- [ ] Install: `pip install pdfplumber`
- [ ] `backend/services/pdf_service.py` — extract text preserving Arabic/RTL
- [ ] Handle multi-page, return page-by-page text
- [ ] Install: `pip install easyocr`
- [ ] `backend/services/ocr_service.py` — OCR scanned PDFs (Arabic, 80+ langs)
- [ ] GPU detection (use CUDA if available, CPU fallback)

### TTS Service
- [ ] Install Piper TTS: `pip install piper-tts`
- [ ] Download voice models for all 10 languages
- [ ] `backend/services/tts_service.py` — generate WAV from text + voice
- [ ] Save audio to `./audio/{project_id}/{chapter_id}.wav`
- [ ] Return duration in seconds
- [ ] Streaming endpoint for real-time playback
- [ ] Install `edge-tts` as fallback: `pip install edge-tts`

### Audio Service
- [ ] Install: `pip install ffmpeg-python pydub`
- [ ] `backend/services/audio_service.py`
- [ ] Convert WAV → MP3 (128kbps / 192kbps / 320kbps)
- [ ] Convert WAV → FLAC (lossless)
- [ ] Merge all chapter audio into single book file
- [ ] Add silence between chapters
- [ ] Background job with progress tracking

### Testing
- [ ] Test PDF extraction with Arabic book
- [ ] Test OCR with scanned Arabic PDF
- [ ] Test Piper TTS for all 10 languages
- [ ] Test export to MP3/WAV/FLAC
- [ ] Test large files (100MB+ PDF)

---

## Phase 2 — React + Vite Frontend

### Setup
- [ ] Create Vite project: `npm create vite@latest frontend -- --template react-ts`
- [ ] Install TailwindCSS v4
- [ ] Install: `npm install axios react-router-dom lucide-react`
- [ ] Configure API base URL pointing to FastAPI (localhost:8000)

### Pages
- [ ] `pages/Home.tsx` — project list + create button
- [ ] `pages/ProjectDetail.tsx` — chapters list + add chapter
- [ ] `pages/Settings.tsx` — TTS settings, voice downloads

### Components
- [ ] `components/projects/ProjectCard.tsx`
- [ ] `components/projects/NewProjectForm.tsx`
- [ ] `components/chapters/ChapterCard.tsx`
- [ ] `components/chapters/NewChapterForm.tsx`
- [ ] `components/chapters/ChapterReorder.tsx` — drag & drop
- [ ] `components/tts/TTSControls.tsx` — language, voice, generate
- [ ] `components/tts/AudioPlayer.tsx` — play/pause/seek/speed
- [ ] `components/pdf/PdfUpload.tsx` — upload + OCR toggle
- [ ] `components/export/ExportModal.tsx` — format, quality, progress

### Features
- [ ] Dark mode toggle
- [ ] RTL support for Arabic/Hebrew
- [ ] Real-time TTS progress (SSE or WebSocket)
- [ ] Audio waveform visualizer
- [ ] Keyboard shortcuts (space = play/pause)
- [ ] Chapter drag & drop reorder

### API Client
- [ ] `lib/api.ts` — typed axios client for all endpoints
- [ ] Error handling + toast notifications
- [ ] Loading states for all async operations

---

## Phase 3 — Tauri Desktop App

### Setup
- [ ] Install Rust: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- [ ] Install Tauri CLI: `npm install -g @tauri-apps/cli`
- [ ] Init Tauri in frontend: `npx tauri init`
- [ ] Configure `tauri.conf.json` (window size, title, icons)

### Python Sidecar
- [ ] Bundle Python backend as Tauri sidecar binary
- [ ] `src-tauri/src/main.rs` — spawn Python FastAPI on app start
- [ ] Auto-find free port
- [ ] Kill Python process on app exit
- [ ] Health check before showing UI

### Tauri Commands
- [ ] Native file picker (open PDF from anywhere on disk)
- [ ] Native save dialog (for audio export)
- [ ] System tray icon + menu
- [ ] Window minimize/maximize/close
- [ ] Auto-update support

### Build
- [ ] Mac `.dmg` installer
- [ ] Windows `.exe` installer
- [ ] Linux `.AppImage`

---

## Phase 4 — Advanced Features

### Voice Cloning
- [ ] Install XTTS v2: `pip install TTS`
- [ ] `backend/services/voice_clone_service.py`
- [ ] Upload 3-second voice sample
- [ ] Clone and generate TTS in cloned voice
- [ ] Save custom voice profiles per project

### Batch Processing
- [ ] Background task queue (FastAPI + asyncio.Queue)
- [ ] Process all chapters in sequence
- [ ] Progress bar per chapter
- [ ] Cancel batch job
- [ ] Email/notification on completion (optional)

### Chapter Auto-Split
- [ ] Detect headings (regex + ML)
- [ ] Split by page number
- [ ] Split by word count target
- [ ] Preview split before applying

### Background Music
- [ ] Upload background track (MP3/WAV)
- [ ] Set volume level (0-100%)
- [ ] Fade in/out
- [ ] Mix with voice using FFmpeg
- [ ] Preview mixed audio

### Additional Formats
- [ ] EPUB parser: `pip install ebooklib`
- [ ] DOCX parser: `pip install python-docx`
- [ ] TXT direct import
- [ ] Drag & drop any file type onto app

### GPU Acceleration
- [ ] Detect CUDA (Nvidia) or Metal (Apple Silicon)
- [ ] Auto-use GPU for Piper TTS inference
- [ ] Speed comparison UI (CPU vs GPU)
- [ ] Settings toggle: force CPU / force GPU / auto

---

## Quick Start Commands

```bash
# Start Docker DB
docker compose up -d

# Start Python backend
cd backend
python -m uvicorn main:app --reload --port 8000

# Start React frontend (dev)
cd frontend
npm run dev

# Build Tauri desktop app
cd frontend
npx tauri build
```

---

## Progress Tracking

| Phase | Status | ETA |
|---|---|---|
| Phase 1 — FastAPI Backend | ⬜ Not started | — |
| Phase 2 — React + Vite Frontend | ⬜ Not started | — |
| Phase 3 — Tauri Desktop | ⬜ Not started | — |
| Phase 4 — Advanced Features | ⬜ Not started | — |
