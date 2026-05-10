# Audiobook Maker

Local-first desktop audiobook maker application. Convert any book (PDF, EPUB, DOCX) to high-quality audio in multiple languages using neural TTS with full privacy - all processing happens locally on your machine.

## Features

### Core Features
- **PDF Text Extraction**: Extract text from PDF files with progress tracking
- **Arabic Text Support**: Special handling for Arabic books with OCR fallback and diacritization (tachkil)
- **Text-to-Speech**: Convert text to natural-sounding speech using Piper TTS
- **Multi-language Support**: Support for 10+ languages including English, Arabic, French, German, Spanish
- **Audio Export**: Export audiobooks in MP3, WAV, or FLAC formats
- **Project Management**: Organize books into projects with multiple chapters
- **Progress Tracking**: Visual progress bars for upload, extraction, and processing

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
- **OCR**: Surya-OCR (primary) + EasyOCR (fallback) with Arabic support
- **TTS**: Multi-engine - Piper (fast), Kokoro (quality), Edge (online)
- **Arabic NLP**: Mishkal for diacritization (tachkil)
- **Job Queue**: ARQ + Redis for async TTS processing
- **Audio**: FFmpeg + Pydub for audio processing
- **Server**: Uvicorn ASGI server

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite with HMR
- **Styling**: TailwindCSS with dark mode support
- **Data Fetching**: TanStack Query (React Query) with caching
- **HTTP Client**: Axios
- **Routing**: React Router DOM
- **Audio**: Wavesurfer.js for waveform editing

### Desktop
- **Framework**: Tauri v2 (Rust-based)
- **Architecture**: Python sidecar (backend) + WebView (frontend)
- **Auto-start**: Backend auto-launches with Tauri app
- **Cross-platform**: Windows, macOS, Linux support

## Project Structure

```
audiobook-maker/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── models/
│   │   └── database.py         # SQLAlchemy models and database setup
│   ├── routers/
│   │   ├── arabic.py           # Arabic text processing endpoints
│   │   ├── chapters.py         # Chapter management API
│   │   ├── export.py           # Audio export functionality
│   │   ├── pdf.py              # PDF extraction and OCR
│   │   ├── projects.py         # Project management API
│   │   └── tts.py              # Text-to-speech endpoints
│   ├── services/
│   │   └── tts_generator.py    # TTS generation service
│   └── requirements.txt        # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AudioPlayer.tsx # Audio playback component
│   │   │   ├── PdfUpload.tsx   # PDF upload with progress
│   │   │   └── TTSControls.tsx # TTS configuration UI
│   │   ├── lib/
│   │   │   └── api.ts          # API client with all endpoints
│   │   ├── pages/
│   │   │   ├── Home.tsx        # Project listing page
│   │   │   └── ProjectDetail.tsx # Chapter management page
│   │   ├── types/
│   │   │   └── audiobook.ts    # TypeScript type definitions
│   │   ├── App.tsx             # Main app with routing
│   │   └── main.tsx            # React entry point
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts          # Vite config with API proxy
│
├── PLAN.md                     # Architecture planning document
├── CHECKLIST.md                # Implementation checklist
└── README.md                   # This file
```

## Quick Start (Recommended)

The easiest way to get started:

```bash
# Clone/navigate to project
cd /Users/tahar/CascadeProjects/audiobook-maker

# Start everything (backend + frontend)
./start.sh web
```

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

### Chapters API
- `GET /api/chapters/?project_id={id}` - List chapters in project
- `POST /api/chapters/` - Create new chapter
- `PUT /api/chapters/{id}` - Update chapter
- `DELETE /api/chapters/{id}` - Delete chapter

### PDF API
- `POST /api/pdf/extract/` - Extract text from PDF
- `POST /api/pdf/ocr/` - OCR for scanned PDFs (supports Arabic)

### Arabic Processing API
- `POST /api/arabic/process/` - Process Arabic text
- `POST /api/arabic/diacritize/` - Add diacritics (tachkil) to Arabic text

### TTS API
- `POST /api/tts/generate/` - Generate audio from text
- `POST /api/tts/preview/` - Preview voice

### Export API
- `POST /api/export/{project_id}/` - Export project to audio file

Full API documentation available at `http://localhost:8001/docs` when backend is running.

## Configuration

### Environment Variables (Backend)

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5434/audiobook

# Audio storage
AUDIO_DIR=./audio

# TTS Models directory
PIPER_MODELS_DIR=./models

# CORS origins (for development)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
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
- `easyocr` - Optical character recognition
- `mishkal` - Arabic diacritization
- `piper-tts` - Text-to-speech engine
- `uvicorn` - ASGI server

### Key Frontend Dependencies
- `react` - UI framework
- `react-router-dom` - Routing
- `axios` - HTTP client
- `lucide-react` - Icons
- `tailwindcss` - Styling
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
- **projects**: id, name, description, language, created_at, updated_at
- **chapters**: id, project_id, title, content, audio_url, order, created_at, updated_at
- **tts_cache**: id, text_hash, audio_path, voice_id, created_at

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- [Piper TTS](https://github.com/rhasspy/piper) - Fast, local neural text-to-speech
- [Mishkal](https://github.com/linuxscout/mishkal) - Arabic text diacritization
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - Multilingual OCR
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF text extraction

## Support

For issues and feature requests, please use the GitHub issue tracker.

---

**Built with ❤️ for audiobook enthusiasts worldwide**
