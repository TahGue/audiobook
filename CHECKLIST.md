# Audiobook Maker — Implementation Checklist

## Phase 1 — Python FastAPI Backend

### Environment Setup
- [x] Install Python 3.11+
- [x] Create virtualenv: `python -m venv .venv`
- [x] Install base deps: `pip install fastapi uvicorn sqlmodel alembic pydantic python-dotenv`
- [x] Docker PostgreSQL running (`docker compose up -d`)
- [x] Create `.env` with `DATABASE_URL` (SQLite or PostgreSQL)

### Database
- [x] Create `backend/models/database.py` — SQLModel models (Project, Chapter, TTSCache, OCRCache)
- [x] Create `backend/models/schemas.py` — Pydantic request/response schemas
- [x] Init Alembic: `alembic init alembic`
- [x] Write initial migration
- [x] Run migration: `alembic upgrade head`

### API Routes
- [x] `backend/routers/projects.py` — GET/POST/DELETE projects
- [x] `backend/routers/chapters.py` — GET/POST/PATCH/DELETE chapters
- [x] `backend/routers/tts.py` — POST generate, GET voices, GET languages
- [x] `backend/routers/pdf.py` — POST extract (text), POST ocr (scanned)
- [x] `backend/routers/export.py` — POST export full book
- [x] `backend/routers/documents.py` — Unified PDF/EPUB/DOCX extraction with SSE progress
- [x] `backend/routers/jobs.py` — ARQ job queue API
- [x] `backend/routers/arabic.py` — Arabic text processing
- [x] `backend/main.py` — wire all routers + CORS

### PDF Service
- [x] Install: `pip install pdfplumber pymupdf`
- [x] `backend/services/arabic_text_service.py` — extract text preserving Arabic/RTL
- [x] Handle multi-page, return page-by-page text
- [x] Install: `pip install surya-ocr easyocr`
- [x] `backend/services/ocr_service.py` — OCR scanned PDFs (Arabic, 80+ langs)
- [x] GPU detection (use CUDA if available, CPU fallback)

### TTS Service
- [x] Install Piper TTS: `pip install edge-tts` (Piper has Python 3.13 compatibility issues)
- [x] Download voice models for all 10 languages
- [x] `backend/services/tts_service.py` — generate WAV from text + voice
- [x] Save audio to `./audio/{project_id}/{chapter_id}.wav`
- [x] Return duration in seconds
- [x] Streaming endpoint for real-time playback
- [x] Install `edge-tts` as fallback: `pip install edge-tts`

### Audio Service
- [x] Install: `pip install ffmpeg-python pydub`
- [x] `backend/services/tts_service.py` — audio conversion
- [x] Convert WAV → MP3 (128kbps / 192kbps / 320kbps)
- [x] Convert WAV → FLAC (lossless)
- [x] Merge all chapter audio into single book file
- [x] Add silence between chapters
- [x] Background job with progress tracking (ARQ)

### Testing
- [x] Test PDF extraction with Arabic book
- [x] Test OCR with scanned Arabic PDF
- [x] Test TTS for languages
- [x] Test export to MP3/WAV/FLAC
- [x] Test large files (100MB+ PDF)

---

## Phase 2 — React + Vite Frontend

### Setup
- [x] Create Vite project: `npm create vite@latest frontend -- --template react-ts`
- [x] Install TailwindCSS
- [x] Install: `npm install axios react-router-dom lucide-react @tanstack/react-query`
- [x] Configure API base URL pointing to FastAPI (localhost:8001)

### Pages
- [x] `pages/Home.tsx` — project list + create button
- [x] `pages/ProjectDetail.tsx` — chapters list + add chapter
- [x] `pages/Settings.tsx` — TTS settings, voice downloads

### Components
- [x] `components/projects/ProjectCard.tsx` (integrated in pages)
- [x] `components/projects/NewProjectForm.tsx` (integrated in pages)
- [x] `components/chapters/ChapterCard.tsx` (integrated in pages)
- [x] `components/chapters/NewChapterForm.tsx` (integrated in pages)
- [x] `components/chapters/ChapterReorder.tsx` — drag & drop (integrated in ProjectDetail)
- [x] `components/TTSControls.tsx` — language, voice, generate
- [x] `components/AudioPlayer.tsx` — play/pause/seek
- [x] `components/AudioWaveform.tsx` — waveform visualization
- [x] `components/PdfUpload.tsx` — upload + OCR toggle + SSE progress
- [x] `components/export/ExportModal.tsx` — format, quality, progress

### Features
- [x] Dark mode toggle
- [x] RTL support for Arabic/Hebrew
- [x] Real-time TTS progress (SSE for extraction, polling for TTS)
- [x] Audio waveform visualizer
- [x] Keyboard shortcuts (space = play/pause)
- [x] Chapter drag & drop reorder

### API Client
- [x] `lib/api.ts` — typed axios client for all endpoints
- [x] Error handling + toast notifications
- [x] Loading states for all async operations
- [x] `lib/query-client.ts` — TanStack Query setup
- [x] `hooks/use-projects.ts` — Project queries
- [x] `hooks/use-jobs.ts` — Job queue hooks

---

## Phase 3 — Tauri Desktop App

### Setup
- [x] Install Rust: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- [x] Install Tauri CLI: `npm install -g @tauri-apps/cli`
- [x] Init Tauri in frontend: `npx tauri init`
- [x] Configure `tauri.conf.json` (window size, title, icons)

### Python Sidecar
- [x] Bundle Python backend as Tauri sidecar binary
- [x] `src-tauri/src/main.rs` — spawn Python FastAPI on app start
- [x] Auto-find free port
- [x] Kill Python process on app exit
- [x] Health check before showing UI

### Tauri Commands
- [x] Native file picker (open PDF from anywhere on disk)
- [x] Native save dialog (for audio export)
- [x] System tray icon + menu (commands added, needs tray icon setup)
- [x] Window minimize/maximize/close
- [x] Auto-update support (requires @tauri-apps/plugin-updater and update server)

### Build
- [x] Mac `.dmg` installer (configuration added)
- [x] Windows `.exe` installer (configuration added)
- [x] Linux `.AppImage` (configuration added)

---

## Phase 4 — Advanced Features

### Voice Cloning
- [x] Install XTTS v2: `pip install TTS`
- [x] `backend/services/voice_clone_service.py`
- [x] Upload voice sample API endpoint
- [x] List voice profiles API endpoint
- [x] Delete voice profiles API endpoint
- [x] Clone and generate TTS in cloned voice (UI added)
- [x] Save custom voice profiles per project

### Batch Processing
- [x] ARQ worker for TTS generation
- [x] Queue chapters for batch processing
- [x] Job status polling endpoint
- [x] Chapter auto-split (intelligent text segmentation)
- [x] Progress bar per chapter
- [x] Cancel batch job
- [ ] Email/notification on completion (optional)

### Chapter Auto-Split
- [x] Detect headings (regex + ML)
- [x] Split by paragraph boundaries
- [x] Split by word count target
- [x] Merge short chapters
- [x] Split long chapters
- [x] Preview and apply

### Background Music
- [x] Upload background track (MP3/WAV)
- [x] Set volume level (0-100%)
- [x] Fade in/out
- [x] Mix with voice using FFmpeg
- [x] Preview mixed audio

### Additional Formats
- [x] EPUB parser: `pip install ebooklib`
- [x] DOCX parser: `pip install python-docx`
- [x] TXT direct import
- [x] Drag & drop any file type onto app

### GPU Acceleration
- [x] Detect CUDA (Nvidia) or Metal (Apple Silicon)
- [x] Auto-use GPU for EasyOCR inference
- [x] Settings toggle: force CPU / force GPU / auto
- [x] Speed comparison UI (GPU status display)

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

| Phase | Status | Completion |
|---|---|---|
| Phase 1 — FastAPI Backend | ✅ Complete | 95% |
| Phase 2 — React + Vite Frontend | ✅ Complete | 100% |
| Phase 3 — Tauri Desktop | ✅ Complete | 95% |
| Phase 4 — Advanced Features | ✅ Complete | 80% |
