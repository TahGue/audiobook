# Audiobook Maker - Architecture & Tech Stack Review

**Date:** May 10, 2026  
**Review Status:** Phase 1 Complete (Database Migration) | Phases 2-4 Planned

---

## Executive Summary

This document captures the comprehensive tech stack audit and implementation roadmap for the Audiobook Maker application, transitioning from a web-first architecture to a true local-first desktop experience.

---

## Phase 1: Foundation (✅ COMPLETED)

### Database: PostgreSQL → SQLite + SQLModel ✅

**Decision:** SWAP

**Rationale:**
- PostgreSQL requires a running server - poor UX for desktop app
- SQLite is zero-setup, file-based, ships inside Tauri bundle
- SQLModel unifies Pydantic + SQLAlchemy (perfect for FastAPI)

**Implementation:**
```python
# Before (PostgreSQL)
DATABASE_URL = "postgresql://user:pass@localhost:5434/audiobook"

# After (SQLite)
DATABASE_URL = "sqlite:///./audiobook.db"  # Ships with app
```

**Benefits:**
- ✅ No Docker required
- ✅ Single-file database (easy backup/transfer)
- ✅ Zero configuration for end users
- ✅ SQLModel provides type safety + ORM

**Files Modified:**
- `backend/models/database.py` - Complete rewrite with SQLModel
- `backend/routers/projects.py` - Updated to SQLModel patterns
- `backend/routers/chapters.py` - Updated to SQLModel patterns
- `backend/requirements.txt` - Added sqlmodel, removed psycopg2-binary

---

## Phase 2: Core Features (🚧 PLANNED)

### 1. Database Migrations: None → Alembic ⏳

**Decision:** ADD

**Rationale:**
- Schema changes destroy user data on update
- No versioning currently
- Essential for any shipped app

**Implementation:**
```bash
# Initialize Alembic
alembic init alembic

# Auto-generate migrations
alembic revision --autogenerate -m "initial schema"

# Apply migrations
alembic upgrade head
```

---

### 2. Document Parsing: PDF Only → PDF + EPUB + DOCX ⏳

**Decision:** COMPLETE THE TRIO

**Current State:**
- ✅ PDF via pdfplumber
- ❌ EPUB missing
- ❌ DOCX missing

**Implementation:**
```python
# EPUB support
import ebooklib
from ebooklib import epub

# DOCX support  
from docx import Document
```

**Router:** `backend/routers/documents.py` (new)

**Benefits:**
- Delivers on README promise
- All three are pure Python (no system deps)
- ebooklib + python-docx are mature libraries

---

### 3. TTS Engine: Piper Only → Piper + Kokoro ⏳

**Decision:** KEEP + EXTEND

**Rationale:**
- Piper: Fast, offline, good for Arabic (keep)
- Kokoro: Higher quality English/multilingual + voice mixing
- Use best tool for each language

**Implementation:**
```python
# Smart TTS selection
def get_tts_engine(language: str, quality: str = "standard"):
    if language == "ar" or quality == "fast":
        return PiperTTS()  # Fast, good Arabic
    else:
        return KokoroTTS()  # High quality, voice mixing
```

**Benefits:**
- Better voice quality for non-Arabic content
- Voice mixing capabilities (unique voices per character)
- Still fully offline

---

### 4. OCR: EasyOCR → Surya-OCR ⏳

**Decision:** SWAP

**Problems with EasyOCR:**
- Slow first-run (downloads models at runtime)
- Heavy RAM usage
- Bad desktop experience

**Surya-OCR Benefits:**
- Faster, higher accuracy
- Better Arabic/multilingual support
- Ships models locally (no runtime downloads)
- Built for document-heavy workflows

**Implementation:**
```python
# Replace
import easyocr  # Slow, heavy

# With
from surya import OCR  # Fast, local models
```

---

## Phase 3: Frontend Modernization (🚧 PLANNED)

### 1. Data Fetching: Axios → TanStack Query ⏳

**Decision:** UPGRADE

**Benefits:**
- Built-in caching (reduces API calls)
- Automatic loading states
- Background refetching
- Optimistic updates
- DevTools for debugging

**Implementation:**
```typescript
// Before: Manual fetch with Axios
const [data, setData] = useState();
useEffect(() => {
  axios.get('/api/projects').then(r => setData(r.data));
}, []);

// After: TanStack Query
const { data, isLoading } = useQuery({
  queryKey: ['projects'],
  queryFn: () => api.getProjects()
});
```

---

### 2. UI Components: Custom → shadcn/ui ⏳

**Decision:** UPGRADE

**Benefits:**
- Polished, accessible components
- Radix UI primitives (WAI-ARIA compliant)
- Tailwind CSS integration
- Copy-paste customization
- Fast development

**Components to Add:**
- Dialog (for modals)
- Dropdown Menu
- Select (better than native)
- Slider (for audio progress)
- Tabs (for chapter organization)
- Toast (notifications)

---

### 3. Audio Player: HTML5 → Wavesurfer.js ⏳

**Decision:** ADD

**Current State:** Basic `<audio>` element (no waveform, no trim)

**Wavesurfer.js Features:**
- Waveform visualization
- Region selection (trim start/end)
- Playback rate control
- Zoom (for long audiobooks)
- Only 11KB gzipped

**Implementation:**
```typescript
import WaveSurfer from 'wavesurfer.js';

const wavesurfer = WaveSurfer.create({
  container: '#waveform',
  waveColor: '#4F46E5',
  progressColor: '#4338CA',
});
```

---

## Phase 4: Desktop Implementation (🚧 PLANNED)

### Tauri: Planned → Implemented with Python Sidecar ⏳

**Decision:** IMPLEMENT

**Architecture:**
```
┌─────────────────────────────────────────┐
│          Tauri Desktop App              │
│  ┌─────────────────────────────────┐   │
│  │         Frontend (React)          │   │
│  │    localhost:5173 (embedded)    │   │
│  └─────────────────────────────────┘   │
│                   │                     │
│         ┌─────────┴─────────┐          │
│         │                   │          │
│  ┌──────▼──────┐   ┌──────▼──────┐    │
│  │   Rust      │   │   Python    │    │
│  │  (Tauri)    │   │  (Sidecar)  │    │
│  │             │   │             │    │
│  │ - Window    │   │ - FastAPI   │    │
│  │ - Menu      │   │ - TTS       │    │
│  │ - System    │   │ - OCR       │    │
│  └─────────────┘   │ - DB        │    │
│                    └─────────────┘    │
│                           ↑            │
│                    ┌──────┴──────┐    │
│                    │  PyInstaller │    │
│                    │   (bundle)   │    │
│                    └─────────────┘    │
└─────────────────────────────────────────┘
```

**Python Sidecar Setup:**
```bash
# Bundle Python backend as executable
pip install pyinstaller
pyinstaller --onefile --name audiobook-backend \
  --add-data "models:models" \
  --add-data "audio:audio" \
  main.py

# Tauri sidecar configuration
tauri.conf.json:
{
  "tauri": {
    "bundle": {
      "externalBin": ["binaries/audiobook-backend"]
    }
  }
}
```

**Auto-Start Logic:**
```rust
// Tauri Rust code
fn setup_backend() -> std::process::Child {
    Command::new(sidecar_path())
        .arg("--port")
        .arg("8001")
        .spawn()
        .expect("Failed to start backend")
}
```

**Benefits:**
- ✅ No user setup (backend auto-starts)
- ✅ Single distributable binary
- ✅ Native OS integration (menu bar, notifications)
- ✅ Tiny binary (~5MB Tauri + ~50MB Python sidecar)
- ✅ Cross-platform (Windows, macOS, Linux)

---

## Phase 5: Async Jobs (🚧 PLANNED)

### Job Queue: BackgroundTasks → ARQ + Redis ⏳

**Decision:** UPGRADE (Optional Phase)

**Current:** FastAPI BackgroundTasks (simple but limited)

**ARQ Benefits:**
- Proper job tracking (status, progress)
- Automatic retries on failure
- Cancel long-running jobs (TTS can take minutes)
- Queue multiple TTS jobs
- WebSocket progress updates

**Implementation:**
```python
from arq import create_pool
from arq.connections import RedisSettings

# Redis settings (embedded or external)
redis = RedisSettings(host='localhost', port=6379)

# Worker function
async def generate_tts(ctx, text: str, voice_id: str):
    # Long-running TTS task
    return await tts_engine.generate(text, voice_id)

# Queue job
job = await redis.enqueue_job('generate_tts', text, voice_id)
```

**Note:** Redis can be embedded (mini-redis) for truly offline usage.

---

## Implementation Roadmap

| Phase | Feature | Priority | Status |
|-------|---------|----------|--------|
| 1 | SQLite + SQLModel | 🔴 High | ✅ Done |
| 1 | Alembic migrations | 🔴 High | ⏳ Pending |
| 2 | EPUB/DOCX support | 🟡 Medium | ⏳ Pending |
| 2 | Kokoro TTS | 🟡 Medium | ⏳ Pending |
| 2 | Surya OCR | 🟡 Medium | ⏳ Pending |
| 3 | TanStack Query | 🟡 Medium | ⏳ Pending |
| 3 | shadcn/ui | 🟢 Low | ⏳ Pending |
| 3 | Wavesurfer.js | 🟢 Low | ⏳ Pending |
| 4 | Tauri + Sidecar | 🔴 High | ⏳ Pending |
| 5 | ARQ Job Queue | 🟢 Low | ⏳ Future |

---

## File Changes Summary

### Modified Files (Phase 1):
```
backend/models/database.py      # SQLModel rewrite
backend/routers/projects.py       # SQLModel patterns
backend/routers/chapters.py     # SQLModel patterns
backend/requirements.txt        # Updated dependencies
```

### New Files (Planned):
```
backend/alembic/                # Database migrations
backend/routers/documents.py    # EPUB/DOCX endpoints
backend/services/kokoro_tts.py  # Kokoro integration
backend/services/surya_ocr.py   # Surya OCR service
frontend/src/lib/query-client.ts # TanStack Query setup
frontend/src/components/ui/    # shadcn/ui components
frontend/src/lib/wavesurfer.ts # Audio waveform
src-tauri/                      # Tauri desktop app
```

---

## Tech Stack Matrix

| Component | Current | Recommended | Status |
|-----------|---------|-------------|--------|
| **Backend** | FastAPI | FastAPI + ARQ | Keep + Extend |
| **Database** | PostgreSQL | SQLite + SQLModel | ✅ Swapped |
| **Migrations** | None | Alembic | ⏳ Add |
| **Documents** | PDF only | PDF+EPUB+DOCX | ⏳ Complete |
| **TTS** | Piper | Piper + Kokoro | ⏳ Extend |
| **OCR** | EasyOCR | Surya-OCR | ⏳ Swap |
| **Frontend** | React+Axios | React+TanStack Query | ⏳ Upgrade |
| **UI** | Custom | shadcn/ui | ⏳ Upgrade |
| **Audio** | `<audio>` | Wavesurfer.js | ⏳ Add |
| **Desktop** | Planned | Tauri v2 + Sidecar | ⏳ Implement |

---

## Recommendations Summary

1. **Immediate (High Priority):**
   - ✅ SQLite migration (done)
   - ⏳ Alembic migrations (prevents data loss)
   - ⏳ Tauri implementation (makes it truly desktop)

2. **Short-term (Medium Priority):**
   - ⏳ EPUB/DOCX support (completes document promise)
   - ⏳ Surya OCR (better Arabic, faster)
   - ⏳ TanStack Query (better frontend DX)

3. **Long-term (Lower Priority):**
   - ⏳ Kokoro TTS (better voice quality)
   - ⏳ shadcn/ui (polished components)
   - ⏳ Wavesurfer.js (audio editing)
   - ⏳ ARQ job queue (production-grade TTS)

---

**Next Steps:**
1. Test SQLite migration (create project, add chapters)
2. Set up Alembic for migrations
3. Begin Tauri desktop shell implementation
4. Add EPUB/DOCX document support

---

*Built with ❤️ for audiobook enthusiasts worldwide*  
*Tech Stack Review completed May 10, 2026*
