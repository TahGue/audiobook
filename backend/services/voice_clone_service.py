"""
Voice Cloning Service

Uses XTTS v2 for voice cloning capabilities.
Allows users to upload voice samples and generate TTS in cloned voices.
"""
import os
import torch
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VoiceProfile:
    """Represents a cloned voice profile."""
    id: str
    name: str
    sample_path: str
    language: str
    created_at: str


class VoiceCloneService:
    """Service for voice cloning using XTTS v2."""
    
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.voice_profiles: dict[str, VoiceProfile] = {}
        self.voices_dir = "voice_samples"
        
        # Create voices directory if it doesn't exist
        os.makedirs(self.voices_dir, exist_ok=True)
        
    def load_model(self):
        """Load the XTTS model lazily when needed."""
        if self.model is None:
            try:
                from TTS.api import TTS
                self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
                logger.info(f"XTTS model loaded on {self.device}")
            except ImportError:
                logger.warning("TTS library not installed. Voice cloning unavailable.")
                raise ImportError("TTS library not installed. Install with: pip install TTS")
            except Exception as e:
                logger.error(f"Failed to load XTTS model: {e}")
                raise
    
    def create_voice_profile(self, sample_path: str, name: str, language: str = "en") -> VoiceProfile:
        """
        Create a voice profile from a sample audio file.
        
        Args:
            sample_path: Path to voice sample audio file
            name: Name for the voice profile
            language: Language code (default: en)
            
        Returns:
            VoiceProfile object
        """
        # Validate sample exists
        if not os.path.exists(sample_path):
            raise FileNotFoundError(f"Voice sample not found: {sample_path}")
        
        # Generate unique ID
        voice_id = f"{name}_{language}_{len(self.voice_profiles)}"
        
        # Create profile
        profile = VoiceProfile(
            id=voice_id,
            name=name,
            sample_path=sample_path,
            language=language,
            created_at=None  # Would use datetime.now() in production
        )
        
        self.voice_profiles[voice_id] = profile
        logger.info(f"Created voice profile: {name} ({voice_id})")
        
        return profile
    
    def generate_speech(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        language: str = "en"
    ) -> str:
        """
        Generate speech using a cloned voice.
        
        Args:
            text: Text to synthesize
            voice_id: ID of the voice profile to use
            output_path: Path to save generated audio
            language: Language code
            
        Returns:
            Path to generated audio file
        """
        if voice_id not in self.voice_profiles:
            raise ValueError(f"Voice profile not found: {voice_id}")
        
        profile = self.voice_profiles[voice_id]
        
        # Load model if not already loaded
        self.load_model()
        
        try:
            # Generate speech with voice cloning
            self.model.tts_to_file(
                text=text,
                speaker_wav=profile.sample_path,
                language=language,
                file_path=output_path
            )
            
            logger.info(f"Generated speech for voice {voice_id}: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            raise
    
    def list_voice_profiles(self) -> list[VoiceProfile]:
        """List all available voice profiles."""
        return list(self.voice_profiles.values())
    
    def delete_voice_profile(self, voice_id: str) -> bool:
        """Delete a voice profile."""
        if voice_id in self.voice_profiles:
            del self.voice_profiles[voice_id]
            logger.info(f"Deleted voice profile: {voice_id}")
            return True
        return False
    
    def is_available(self) -> bool:
        """Check if voice cloning is available."""
        try:
            self.load_model()
            return True
        except:
            return False


# Singleton instance
voice_clone_service = VoiceCloneService()
