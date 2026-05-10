"""TTS Service supporting multiple engines: Piper and Kokoro."""

import os
import hashlib
import tempfile
from typing import Optional, Dict, List
from pathlib import Path
from enum import Enum


class TTSEngine(Enum):
    """Available TTS engines."""
    PIPER = "piper"
    KOKORO = "kokoro"
    EDGE = "edge"  # Fallback for online voices


class Voice:
    """TTS Voice configuration."""
    def __init__(
        self,
        id: str,
        name: str,
        language: str,
        engine: TTSEngine,
        model_path: Optional[str] = None,
        config_path: Optional[str] = None,
        quality: str = "medium"
    ):
        self.id = id
        self.name = name
        self.language = language
        self.engine = engine
        self.model_path = model_path
        self.config_path = config_path
        self.quality = quality


class TTSService:
    """Unified TTS service supporting multiple engines."""
    
    def __init__(self, cache_dir: str = "./audio/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.voices: Dict[str, Voice] = {}
        self._initialize_voices()
    
    def _initialize_voices(self):
        """Initialize available voices for each engine."""
        # Piper voices (fast, good for Arabic)
        self.voices.update({
            "piper-en": Voice(
                id="piper-en",
                name="Piper English",
                language="en",
                engine=TTSEngine.PIPER,
                quality="fast"
            ),
            "piper-ar": Voice(
                id="piper-ar",
                name="Piper Arabic",
                language="ar",
                engine=TTSEngine.PIPER,
                quality="fast"
            ),
        })
        
        # Kokoro voices (high quality, multilingual)
        # Note: Kokoro models need to be downloaded separately
        self.voices.update({
            "kokoro-en": Voice(
                id="kokoro-en",
                name="Kokoro English",
                language="en",
                engine=TTSEngine.KOKORO,
                quality="high"
            ),
            "kokoro-multilang": Voice(
                id="kokoro-multilang",
                name="Kokoro Multilingual",
                language="multilingual",
                engine=TTSEngine.KOKORO,
                quality="high"
            ),
        })
        
        # Edge TTS voices (online, Microsoft neural voices)
        self.voices.update({
            "edge-en": Voice(
                id="edge-en",
                name="Microsoft English (Online)",
                language="en",
                engine=TTSEngine.EDGE,
                quality="high"
            ),
            "edge-ar": Voice(
                id="edge-ar",
                name="Microsoft Arabic (Online)",
                language="ar",
                engine=TTSEngine.EDGE,
                quality="high"
            ),
        })
    
    def get_voices(self, language: Optional[str] = None) -> List[Voice]:
        """Get available voices, optionally filtered by language."""
        voices = list(self.voices.values())
        if language:
            voices = [v for v in voices if v.language == language or v.language == "multilingual"]
        return voices
    
    def get_best_voice(self, language: str, prefer_quality: bool = False) -> Voice:
        """Get the best voice for a language.
        
        Args:
            language: Language code (e.g., 'en', 'ar')
            prefer_quality: If True, prefer Kokoro; else prefer Piper for speed
        """
        if language == "ar":
            # For Arabic, Piper is currently more reliable
            return self.voices.get("piper-ar", self.voices["edge-ar"])
        
        if prefer_quality:
            # Prefer Kokoro for quality
            voice = self.voices.get(f"kokoro-{language}")
            if voice:
                return voice
        
        # Fall back to Piper for speed, then Edge
        voice = self.voices.get(f"piper-{language}")
        if voice:
            return voice
        
        return self.voices.get(f"edge-{language}", self.voices["edge-en"])
    
    def _get_cache_path(self, text: str, voice_id: str) -> Path:
        """Generate cache file path based on text hash and voice."""
        text_hash = hashlib.md5(f"{text}:{voice_id}".encode()).hexdigest()
        return self.cache_dir / f"{voice_id}_{text_hash}.wav"
    
    def generate(
        self,
        text: str,
        voice_id: str,
        use_cache: bool = True
    ) -> str:
        """Generate audio for text using specified voice.
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            use_cache: Whether to use cached audio if available
            
        Returns:
            Path to generated audio file
        """
        voice = self.voices.get(voice_id)
        if not voice:
            raise ValueError(f"Unknown voice: {voice_id}")
        
        # Check cache
        cache_path = self._get_cache_path(text, voice_id)
        if use_cache and cache_path.exists():
            return str(cache_path)
        
        # Generate based on engine
        if voice.engine == TTSEngine.PIPER:
            output_path = self._generate_piper(text, voice, cache_path)
        elif voice.engine == TTSEngine.KOKORO:
            output_path = self._generate_kokoro(text, voice, cache_path)
        elif voice.engine == TTSEngine.EDGE:
            output_path = self._generate_edge(text, voice, cache_path)
        else:
            raise ValueError(f"Unsupported engine: {voice.engine}")
        
        return str(output_path)
    
    def _generate_piper(self, text: str, voice: Voice, output_path: Path) -> Path:
        """Generate audio using Piper TTS."""
        import piper
        
        # Initialize Piper with voice model
        synthesizer = piper.PiperVoice.load(
            model_path=voice.model_path or "./models/piper-voice.onnx",
            config_path=voice.config_path
        )
        
        # Generate audio
        with open(output_path, 'wb') as f:
            synthesizer.synthesize(text, f)
        
        return output_path
    
    def _generate_kokoro(self, text: str, voice: Voice, output_path: Path) -> Path:
        """Generate audio using Kokoro TTS."""
        try:
            from kokoro import KPipeline
            
            # Initialize Kokoro pipeline
            pipeline = KPipeline(lang_code=voice.language[:2] if voice.language != "multilingual" else 'a')
            
            # Generate audio
            generator = pipeline(
                text,
                voice=voice.model_path or "af",  # Default voice
                speed=1.0
            )
            
            # Save audio
            import torchaudio
            for i, (gs, ps, audio) in enumerate(generator):
                torchaudio.save(output_path, audio, 24000)
                break  # Just first segment for now
            
            return output_path
        except ImportError:
            raise ImportError(
                "Kokoro not installed. Install with: pip install kokoro "
                "or use a Piper voice instead."
            )
    
    def _generate_edge(self, text: str, voice: Voice, output_path: Path) -> Path:
        """Generate audio using Microsoft Edge TTS (online)."""
        import edge_tts
        import asyncio
        
        async def _generate():
            voice_name = "en-US-GuyNeural" if voice.language == "en" else "ar-SA-HamedNeural"
            communicate = edge_tts.Communicate(text, voice_name)
            await communicate.save(str(output_path))
        
        asyncio.run(_generate())
        return output_path
    
    def preview_voice(self, voice_id: str) -> str:
        """Generate a preview sample for a voice."""
        voice = self.voices.get(voice_id)
        if not voice:
            raise ValueError(f"Unknown voice: {voice_id}")
        
        # Sample text based on language
        samples = {
            "en": "Hello! This is a preview of my voice. I can read any book you upload.",
            "ar": "مرحباً! هذا نموذج من صوتي. يمكنني قراءة أي كتاب تقوم برفعه.",
        }
        
        text = samples.get(voice.language, samples["en"])
        return self.generate(text, voice_id, use_cache=False)


# Global TTS service instance
tts_service = TTSService()
