"""
One-Click Audiobook Service

Orchestrates the entire audiobook generation workflow:
- Document extraction
- Chapter splitting
- Batch TTS generation
- Export with metadata
- Cover art extraction
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from services.chapter_split_service import chapter_split_service
from services.tts_service import tts_service
from services.background_music_service import background_music_service

logger = logging.getLogger(__name__)


@dataclass
class AudiobookConfig:
    """Configuration for one-click audiobook generation."""
    project_id: str
    document_path: str
    voice_id: str
    language: str
    format: str = "mp3"
    quality: str = "192k"
    add_background_music: bool = False
    background_music_volume: int = 50
    auto_split_chapters: bool = True
    target_chapter_length: int = 5000


class OneClickAudiobookService:
    """Service for one-click audiobook generation."""
    
    def __init__(self):
        self.status: Dict[str, Dict[str, Any]] = {}
    
    def generate_audiobook(self, config: AudiobookConfig) -> Dict[str, Any]:
        """
        Generate complete audiobook in one click.
        
        Args:
            config: AudiobookConfig with all settings
            
        Returns:
            Dictionary with generation status and results
        """
        job_id = f"audiobook_{config.project_id}_{datetime.now().timestamp()}"
        
        self.status[job_id] = {
            "status": "started",
            "progress": 0,
            "current_step": "initializing",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error": None,
            "result": None
        }
        
        try:
            # Step 1: Extract text from document
            self._update_status(job_id, "extracting", 10, "Extracting text from document")
            extracted_text = self._extract_document(config.document_path, config.language)
            
            # Step 2: Split into chapters
            self._update_status(job_id, "splitting", 30, "Splitting text into chapters")
            chapters = self._split_into_chapters(extracted_text, config)
            
            # Step 3: Generate TTS for all chapters
            self._update_status(job_id, "generating", 50, "Generating audio for chapters")
            chapter_audio_paths = self._generate_chapter_audio(chapters, config)
            
            # Step 4: Merge and export
            self._update_status(job_id, "exporting", 80, "Exporting complete audiobook")
            output_path = self._export_audiobook(chapter_audio_paths, config)
            
            # Step 5: Generate metadata
            self._update_status(job_id, "metadata", 90, "Generating metadata")
            metadata = self._generate_metadata(config, chapters)
            
            # Step 6: Extract/generate cover art
            self._update_status(job_id, "cover", 95, "Processing cover art")
            cover_path = self._process_cover_art(config.document_path)
            
            # Complete
            self._update_status(job_id, "completed", 100, "Completed")
            self.status[job_id]["completed_at"] = datetime.utcnow().isoformat()
            self.status[job_id]["result"] = {
                "output_path": output_path,
                "metadata": metadata,
                "cover_path": cover_path,
                "chapter_count": len(chapters)
            }
            
            return self.status[job_id]
            
        except Exception as e:
            logger.error(f"One-click audiobook generation failed: {e}")
            self.status[job_id]["status"] = "failed"
            self.status[job_id]["error"] = str(e)
            self.status[job_id]["completed_at"] = datetime.utcnow().isoformat()
            raise
    
    def _extract_document(self, document_path: str, language: str) -> str:
        """Extract text from document (PDF/EPUB/DOCX)."""
        # Use the existing document extraction service
        from services.arabic_text_service import arabic_text_service
        
        try:
            # Try to extract text from PDF
            import pdfplumber
            with pdfplumber.open(document_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            
            # Clean and process the text
            if language == "ar":
                text = arabic_text_service.clean_arabic_text(text)
            
            return text
        except Exception as e:
            logger.error(f"Failed to extract document: {e}")
            raise
    
    def _split_into_chapters(self, text: str, config: AudiobookConfig) -> list[Dict[str, Any]]:
        """Split text into chapters."""
        if config.auto_split_chapters:
            chapters_data = chapter_split_service.split_text(
                text=text,
                language=config.language,
                target_length=config.target_chapter_length
            )
            return chapters_data["chapters"]
        else:
            # Single chapter
            return [{"title": "Chapter 1", "content": text, "index": 0}]
    
    def _generate_chapter_audio(self, chapters: list[Dict[str, Any]], config: AudiobookConfig) -> list[str]:
        """Generate audio for all chapters."""
        audio_paths = []
        total_chapters = len(chapters)
        
        for i, chapter in enumerate(chapters):
            self._update_status(
                f"audiobook_{config.project_id}",
                "generating",
                50 + (i / total_chapters) * 30,
                f"Generating chapter {i + 1}/{total_chapters}"
            )
            
            # Generate audio using TTS service
            audio_path = tts_service.generate(
                text=chapter["content"],
                voice_id=config.voice_id,
                use_cache=True
            )
            audio_paths.append(audio_path)
        
        return audio_paths
    
    def _export_audiobook(self, audio_paths: list[str], config: AudiobookConfig) -> str:
        """Merge and export audiobook."""
        import subprocess
        
        output_filename = f"audiobook_{config.project_id}.{config.format}"
        output_path = os.path.join("./audio", output_filename)
        
        try:
            # Use FFmpeg to concatenate audio files
            # First create a list file for FFmpeg
            list_file = os.path.join("./audio", f"concat_{config.project_id}.txt")
            with open(list_file, 'w') as f:
                for audio_path in audio_paths:
                    f.write(f"file '{os.path.abspath(audio_path)}'\n")
            
            # Build FFmpeg command based on format
            codec_map = {
                'mp3': 'libmp3lame',
                'wav': 'pcm_s16le',
                'flac': 'flac'
            }
            
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-c:a', codec_map.get(config.format, 'libmp3lame'),
                '-b:a', config.quality,
                '-y',
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Clean up list file
            os.remove(list_file)
            
            logger.info(f"Exported audiobook to {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg export failed: {e.stderr}")
            raise RuntimeError(f"Audio export failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg is not installed. Please install FFmpeg to use audiobook export.")
    
    def _generate_metadata(self, config: AudiobookConfig, chapters: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate audiobook metadata."""
        return {
            "title": f"Audiobook {config.project_id}",
            "author": "Unknown",
            "language": config.language,
            "narrator": "AI Voice",
            "duration_seconds": 0,
            "chapter_count": len(chapters),
            "format": config.format,
            "quality": config.quality,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _process_cover_art(self, document_path: str) -> Optional[str]:
        """Extract or generate cover art."""
        try:
            # Try to extract first page as cover image from PDF
            import pdfplumber
            from PIL import Image
            import io
            
            cover_dir = os.path.join("./audio", "covers")
            os.makedirs(cover_dir, exist_ok=True)
            
            # Extract first page as image
            with pdfplumber.open(document_path) as pdf:
                if len(pdf.pages) > 0:
                    first_page = pdf.pages[0]
                    # Convert to image
                    img = first_page.to_image()
                    cover_path = os.path.join(cover_dir, f"cover_{hash(document_path)}.png")
                    img.save(cover_path)
                    logger.info(f"Extracted cover art to {cover_path}")
                    return cover_path
            
            return None
        except Exception as e:
            logger.warning(f"Failed to extract cover art: {e}")
            return None
    
    def _update_status(self, job_id: str, status: str, progress: int, current_step: str):
        """Update job status."""
        if job_id in self.status:
            self.status[job_id]["status"] = status
            self.status[job_id]["progress"] = progress
            self.status[job_id]["current_step"] = current_step
    
    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a generation job."""
        return self.status.get(job_id)


# Singleton instance
one_click_audiobook_service = OneClickAudiobookService()
