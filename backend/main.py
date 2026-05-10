import os
from dotenv import load_dotenv

# Load environment variables before any other imports
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from models.database import create_tables
from routers import projects, chapters, tts, pdf, export, arabic, documents, jobs

app = FastAPI(title="Audiobook Maker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("./audio", exist_ok=True)

@app.on_event("startup")
def on_startup():
    create_tables()

app.mount("/audio", StaticFiles(directory="./audio"), name="audio")

app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(chapters.router, prefix="/api/chapters", tags=["chapters"])
app.include_router(tts.router, prefix="/api/tts", tags=["tts"])
app.include_router(pdf.router, prefix="/api/pdf", tags=["pdf"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(arabic.router, prefix="/api/arabic", tags=["arabic"])

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
