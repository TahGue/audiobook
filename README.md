# Audiobook Maker

Local-first desktop audiobook maker application. Convert any book (PDF, EPUB, DOCX) to high-quality audio in multiple languages using neural TTS with full privacy - all processing happens locally on your machine.

**Status: ✅ 100% Complete - All Features Implemented**

## Features

### Core Features
- **PDF Text Extraction**: Extract text from PDF files with progress tracking
- **Multi-Format Support**: PDF, EPUB, DOCX, and TXT import with drag-and-drop
- **Arabic Text Support**: Special handling for Arabic books with OCR fallback and diacritization (tachkil)
- **Text-to-Speech**: Convert text to natural-sounding speech using Edge TTS
- **Multi-language Support**: Support for 10+ languages including English, Arabic, French, German, Spanish
- **Audio Export**: Export audiobooks in MP3 (128k/192k/320k), WAV, or FLAC formats
- **Project Management**: Organize books into projects with multiple chapters
- **Progress Tracking**: Visual progress bars for upload, extraction, and processing
- **Dark Mode**: System-aware dark mode toggle
- **Keyboard Shortcuts**: Spacebar for play/pause control

### Advanced Features
- **Voice Cloning**: Upload voice samples and clone custom voices using XTTS v2
- **Background Music**: Mix background music with voice audio (volume control, fade in/out)
- **Chapter Auto-Split**: Intelligently split long text into chapters based on headings and paragraphs
- **GPU Acceleration**: Automatic GPU detection for faster OCR and voice cloning
- **Drag-and-Drop Reordering**: Reorder chapters with drag-and-drop interface
- **Batch Processing**: Queue multiple chapters for TTS generation with ARQ
- **Email Notifications**: Receive email notifications when batch jobs complete
- **Custom Voice Profiles**: Associate custom voice profiles with specific projects

### Tauri Desktop Integration
- **Native File Picker**: Use native OS file dialogs for PDF upload
- **Native Save Dialog**: Use native OS save dialogs for audio export
- **System Tray**: Minimize to system tray with menu controls
- **Cross-platform**: Windows, macOS, Linux support with installers

### Arabic-Specific Features
- **Arabic Character Detection**: Automatically detects Arabic text in PDFs
- **OCR Fallback**: When PDF text extraction fails, OCR can extract Arabic from scanned documents
- **Diacritization (Tachkil)**: Add vowel marks (harakat) to Arabic text for better TTS pronunciation
- **Mishkal Integration**: Uses Mishkal library for automatic Arabic diacritization

## Technology Stack

### Backend
- **Framework**: Python FastAPI with async support
- **Database**: SQLite + SQLModel (zero-setup, PostgreSQL optional)
- **Migrations**: Alembic for database schema versioning
- **Document Processing**: pdfplumber (PDF), ebooklib (EPUB), python-docx (DOCX)
- **OCR**: Surya-OCR (primary) + EasyOCR (fallback) with GPU support
- **TTS**: Edge TTS (primary), XTTS v2 (voice cloning)
- **Arabic NLP**: Mishkal for diacritization (tachkil)
- **Job Queue**: ARQ + Redis for async TTS processing
- **Audio**: FFmpeg + Pydub for audio processing
- **GPU**: PyTorch for GPU acceleration
- **Server**: Uvicorn ASGI server

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite with HMR
- **Styling**: TailwindCSS v4 with dark mode support
- **Data Fetching**: TanStack Query (React Query) with caching
- **HTTP Client**: Axios
- **Routing**: React Router DOM v7
- **Audio**: Wavesurfer.js for waveform visualization
- **Drag & Drop**: @dnd-kit for drag-and-drop reordering
- **Icons**: Lucide React

### Desktop
- **Framework**: Tauri v2 (Rust-based)
- **Architecture**: Python sidecar (backend) + WebView (frontend)
- **Auto-start**: Backend auto-launches with Tauri app
- **Native Dialogs**: @tauri-apps/plugin-dialog for file dialogs
- **Cross-platform**: Windows, macOS, Linux support with installers

## Project Structure

```
audiobook-maker/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── models/
│   │   ├── database.py          # SQLAlchemy models and database setup
│   │   └── schemas.py          # Pydantic request/response schemas
│   ├── routers/
│   │   ├── arabic.py            # Arabic text processing endpoints
│   │   ├── chapters.py          # Chapter management API
│   │   ├── documents.py         # Unified document extraction API
│   │   ├── export.py            # Audio export and background music
│   │   ├── jobs.py              # Job queue and notifications
│   │   ├── pdf.py               # PDF extraction and OCR
│   │   ├── projects.py          # Project management API
│   │   └── tts.py               # Text-to-speech and voice cloning
│   ├── services/
│   │   ├── arabic_text_service.py # Arabic text processing
│   │   ├── background_music_service.py # Background music mixing
│   │   ├── chapter_split_service.py   # Chapter auto-split
│   │   ├── notification_service.py     # Email notifications
│   │   ├── ocr_service.py       # OCR processing
│   │   ├── tts_service.py       # TTS generation
│   │   └── voice_clone_service.py     # Voice cloning
│   ├── requirements.txt         # Python dependencies
│   └── start.sh                 # Backend startup script
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AudioPlayer.tsx  # Audio playback component
│   │   │   ├── ExportModal.tsx # Export format/quality modal
│   │   │   ├── PdfUpload.tsx    # PDF upload with drag-and-drop
│   │   │   └── TTSControls.tsx   # TTS configuration UI
│   │   ├── contexts/
│   │   │   └── DarkModeContext.tsx # Dark mode state
│   │   ├── lib/
│   │   │   └── api.ts           # API client with all endpoints
│   │   ├── pages/
│   │   │   ├── Home.tsx          # Project listing page
│   │   │   ├── ProjectDetail.tsx # Chapter management page
│   │   │   └── Settings.tsx      # Settings page
│   │   ├── App.tsx              # Main app with routing
│   │   └── main.tsx             # React entry point
│   ├── src-tauri/
│   │   ├── src/
│   │   │   ├── lib.rs           # Tauri commands and sidecar
│   │   │   └── main.rs          # Tauri app entry point
│   │   ├── capabilities/
│   │   │   └── default.json     # Tauri permissions
│   │   └── tauri.conf.json      # Tauri configuration
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts           # Vite config with API proxy
│
├── docker-compose.yml           # PostgreSQL and Redis containers
├── CHECKLIST.md                 # Implementation checklist
├── PROJECT_STATUS.md            # Project status and progress
└── README.md                    # This file
```

## Quick Start (Recommended)

The easiest way to get started:

```bash
# Clone the repository
git clone https://github.com/TahGue/audiobook.git
cd audiobook

# Start PostgreSQL and Redis (optional, for production)
docker compose up -d

# Start backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8001

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

The web app will be available at `http://localhost:5173`

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- FFmpeg (for audio processing)
- Redis (optional, for job queue)

### 1. Database Setup

**SQLite (Default - Zero Setup)**:
No configuration needed! SQLite database is created automatically at `backend/audiobook.db`.

**PostgreSQL (Optional)**:
If you prefer PostgreSQL, update `backend/.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/audiobook
```

### 2. Backend Setup

**Option A: Using Startup Script (Recommended)**
```bash
cd backend
./start.sh dev        # Development mode
./start.sh prod       # Production mode
./start.sh worker     # ARQ job worker (optional)
```

**Option B: Manual Setup**
```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env if needed (SQLite works out of the box)

# Run database migrations
alembic upgrade head

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

The API will be available at `http://localhost:8001`
API documentation at `http://localhost:8001/docs`

### 3. Frontend Setup

**Option A: Using Main Startup Script**
```bash
./start.sh web          # Web development
./start.sh desktop      # Desktop app (Tauri)
./start.sh all          # Everything (backend + frontend + worker)
```

**Option B: Manual Setup**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev              # Web: http://localhost:5173
npm run tauri:dev        # Desktop app
```

### 4. Desktop App Setup

```bash
cd frontend

# Build Python sidecar first (one-time)
cd ../backend
python3 build_sidecar.py

# Build desktop app
cd ../frontend
npm run tauri:build
```

## Usage Guide

### Creating a Project
1. Open the frontend at `http://localhost:5173`
2. Click "New Project" button
3. Enter project name and description
4. Select preferred language

### Adding Chapters from PDF
1. Open a project
2. Click "Upload PDF" 
3. Select your PDF file
4. Watch the progress bar for upload and extraction
5. If Arabic text is detected, click "Add Diacritics (Tachkil)" to improve pronunciation
6. Extracted text will be added as a new chapter

### Generating Audio
1. Select a chapter
2. Choose voice and language in TTS Controls
3. Click "Generate Audio"
4. Wait for processing (progress shown in UI)
5. Play audio directly in the browser or download

### Exporting Audiobook
1. Go to project settings
2. Select export format (MP3/WAV/FLAC) and quality
3. Click "Export Project"
4. Download the complete audiobook file

## API Documentation

### Projects API
- `GET /api/projects/` - List all projects
- `POST /api/projects/` - Create new project
- `GET /api/projects/{id}` - Get project details
- `DELETE /api/projects/{id}` - Delete project
- `PATCH /api/projects/{id}` - Update project

### Chapters API
- `GET /api/chapters/?project_id={id}` - List chapters in project
- `POST /api/chapters/` - Create new chapter
- `PUT /api/chapters/{id}` - Update chapter
- `DELETE /api/chapters/{id}` - Delete chapter
- `PATCH /api/chapters/{id}/reorder/` - Reorder chapter
- `POST /api/chapters/auto-split` - Auto-split text into chapters

### Documents API
- `POST /api/documents/extract/` - Extract text from PDF/EPUB/DOCX
- `POST /api/documents/ocr/` - OCR for scanned documents

### Arabic Processing API
- `POST /api/arabic/process/` - Process Arabic text
- `POST /api/arabic/diacritize/` - Add diacritics (tachkil) to Arabic text

### TTS API
- `POST /api/tts/generate/` - Generate audio from text
- `GET /api/tts/languages/` - Get supported languages
- `GET /api/tts/voices/` - Get available voices
- `POST /api/tts/voice-profiles` - Create voice profile
- `GET /api/tts/voice-profiles` - List voice profiles
- `DELETE /api/tts/voice-profiles/{id}` - Delete voice profile
- `GET /api/tts/voice-clone/available` - Check voice cloning availability

### Export API
- `POST /api/export/{project_id}` - Export project to audio file
- `POST /api/export/background-music/upload` - Upload background music
- `GET /api/export/background-music/tracks` - List background music
- `POST /api/export/background-music/mix` - Mix background music with voice
- `POST /api/export/background-music/preview` - Preview mixed audio

### Jobs API
- `POST /api/jobs/tts/enqueue` - Enqueue TTS job
- `GET /api/jobs/tts/{job_id}/status` - Get job status
- `POST /api/jobs/tts/{job_id}/cancel` - Cancel job
- `GET /api/jobs/queue/stats` - Get queue statistics
- `GET /api/jobs/notification/status` - Get notification status
- `POST /api/jobs/notification/config` - Update notification config
- `POST /api/jobs/notification/test` - Test notification

Full API documentation available at `http://localhost:8001/docs` when backend is running.

## Configuration

### Environment Variables (Backend)

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5434/audiobook

# Audio storage
AUDIO_DIR=./audio

# OCR/TTS Models directory
MODELS_DIR=./models

# CORS origins (for development)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# GPU acceleration
USE_GPU=true

# Voice cloning
TTS_MODELS_DIR=./tts_models

# Notifications (optional)
NOTIFICATION_EMAIL_ENABLED=false
NOTIFICATION_EMAIL_ADDRESS=your@email.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@email.com
SMTP_PASSWORD=your_password
```

### Vite Proxy Configuration

The frontend `vite.config.ts` includes proxy settings for API calls:

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8001',
    changeOrigin: true,
  },
  '/audio': {
    target: 'http://localhost:8001',
    changeOrigin: true,
  }
}
```

## Development

### Backend Development

```bash
cd backend
source .venv/bin/activate

# Run with auto-reload
uvicorn main:app --reload --port 8001

# Run tests
pytest

# Format code
black .

# Type checking
mypy .
```

### Frontend Development

```bash
cd frontend

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npx tsc --noEmit

# Linting
npm run lint
```

## Troubleshooting

### OCR Not Working
EasyOCR requires model downloads on first use. The first OCR request may timeout while downloading models. Subsequent requests will be faster.

### Arabic Text Not Detected
If Arabic text appears garbled after extraction:
1. Try the "Add Diacritics (Tachkil)" button
2. If text is still garbled, the PDF may have encoding issues - try OCR fallback

### TTS Voice Not Available
Piper TTS models need to be downloaded separately. Place `.onnx` and `.onnx.json` files in the `models/` directory.

### Database Connection Issues
Ensure PostgreSQL is running and the `DATABASE_URL` in `.env` is correct.

## Dependencies

### Key Backend Dependencies
- `fastapi` - Web framework
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL driver
- `pdfplumber` - PDF text extraction
- `pymupdf` - PDF rendering for OCR
- `ebooklib` - EPUB parsing
- `python-docx` - DOCX parsing
- `surya-ocr` - Primary OCR engine
- `easyocr` - Fallback OCR with GPU support
- `mishkal` - Arabic diacritization
- `edge-tts` - Text-to-speech engine
- `TTS` - XTTS v2 voice cloning
- `torch` - PyTorch for GPU acceleration
- `arq` - Job queue for async processing
- `redis` - Redis for job queue
- `ffmpeg-python` - Audio processing
- `pydub` - Audio manipulation
- `uvicorn` - ASGI server

### Key Frontend Dependencies
- `react` - UI framework
- `react-router-dom` - Routing
- `axios` - HTTP client
- `@tanstack/react-query` - Data fetching and caching
- `lucide-react` - Icons
- `tailwindcss` - Styling
- `@dnd-kit/core` - Drag and drop
- `@dnd-kit/sortable` - Sortable drag and drop
- `@tauri-apps/api` - Tauri API
- `@tauri-apps/plugin-dialog` - Native dialogs
- `wavesurfer.js` - Audio waveform visualization
- `vite` - Build tool
- `typescript` - Type safety

## Architecture

### Data Flow
1. User uploads PDF → Frontend
2. Frontend sends PDF to `/api/pdf/extract/` → Backend
3. Backend extracts text using pdfplumber → Returns text
4. Frontend displays extracted text
5. User clicks "Generate Audio" → Frontend sends text to `/api/tts/generate/`
6. Backend generates audio using Piper TTS → Returns audio file URL
7. Frontend plays audio via `<audio>` element

### Database Schema
- **projects**: id, title, description, language, voice_profile_id, created_at, updated_at
- **chapters**: id, project_id, title, content, language, voice_id, order_index, audio_path, duration_seconds, created_at, updated_at
- **tts_cache**: id, text_hash, voice_id, audio_path, created_at
- **ocr_cache**: id, file_hash, language, extracted_text, created_at

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- [Edge TTS](https://github.com/rany2/edge-tts) - Microsoft Edge neural text-to-speech
- [XTTS v2](https://github.com/coqui-ai/TTS) - Voice cloning and TTS
- [Mishkal](https://github.com/linuxscout/mishkal) - Arabic text diacritization
- [Surya-OCR](https://github.com/VikParuchuri/surya) - Multilingual OCR
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - Multilingual OCR
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF text extraction
- [Tauri](https://tauri.app/) - Desktop application framework
- [@dnd-kit](https://dndkit.com/) - Drag and drop library
- [React Query](https://tanstack.com/query) - Data fetching and caching

## Support

For issues and feature requests, please use the GitHub issue tracker.

---

**Built with ❤️ for audiobook enthusiasts worldwide**
