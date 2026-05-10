"""
Background Music Service

Handles mixing background music with voice audio using FFmpeg.
Supports volume control, fade in/out, and audio mixing.
"""
import os
import subprocess
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BackgroundMusicConfig:
    """Configuration for background music mixing."""
    music_path: str
    voice_path: str
    output_path: str
    volume: int = 50  # 0-100
    fade_in_duration: float = 2.0  # seconds
    fade_out_duration: float = 2.0  # seconds


class BackgroundMusicService:
    """Service for mixing background music with voice audio."""
    
    def __init__(self):
        self.music_dir = "background_music"
        os.makedirs(self.music_dir, exist_ok=True)
    
    def mix_audio(self, config: BackgroundMusicConfig) -> str:
        """
        Mix background music with voice audio using FFmpeg.
        
        Args:
            config: BackgroundMusicConfig with paths and settings
            
        Returns:
            Path to the mixed audio file
        """
        # Validate inputs
        if not os.path.exists(config.music_path):
            raise FileNotFoundError(f"Background music not found: {config.music_path}")
        if not os.path.exists(config.voice_path):
            raise FileNotFoundError(f"Voice audio not found: {config.voice_path}")
        
        # Calculate volume as a fraction (0-1)
        volume_fraction = config.volume / 100.0
        
        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-i', config.music_path,
            '-i', config.voice_path,
            '-filter_complex',
            self._build_filter_complex(volume_fraction, config.fade_in_duration, config.fade_out_duration),
            '-map', '[mixed]',
            '-y',  # Overwrite output file
            config.output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Successfully mixed audio: {config.output_path}")
            return config.output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr}")
            raise RuntimeError(f"Audio mixing failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg is not installed. Please install FFmpeg to use background music mixing.")
    
    def _build_filter_complex(self, volume: float, fade_in: float, fade_out: float) -> str:
        """
        Build FFmpeg filter complex string for audio mixing.
        
        Args:
            volume: Music volume as fraction (0-1)
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds
            
        Returns:
            FFmpeg filter complex string
        """
        # Apply volume to music
        volume_filter = f"[0:a]volume={volume}[music]"
        
        # Apply fade in/out to music
        fade_filter = f"[music]afade=t=in:st=0:d={fade_in},afade=t=out:st=-{fade_out}:d={fade_out}[faded_music]"
        
        # Mix music with voice
        mix_filter = f"[faded_music][1:a]amix=inputs=2:duration=first:dropout_transition=2[mixed]"
        
        return f"{volume_filter};{fade_filter};{mix_filter}"
    
    def save_music_track(self, file, filename: str) -> str:
        """
        Save uploaded background music file.
        
        Args:
            file: File object
            filename: Name to save the file as
            
        Returns:
            Path to saved file
        """
        file_path = os.path.join(self.music_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file.read())
        logger.info(f"Saved background music: {file_path}")
        return file_path
    
    def list_music_tracks(self) -> list[str]:
        """List all available background music tracks."""
        if not os.path.exists(self.music_dir):
            return []
        
        tracks = []
        for filename in os.listdir(self.music_dir):
            if filename.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
                tracks.append(filename)
        
        return sorted(tracks)
    
    def delete_music_track(self, filename: str) -> bool:
        """Delete a background music track."""
        file_path = os.path.join(self.music_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted background music: {file_path}")
            return True
        return False
    
    def preview_mix(self, config: BackgroundMusicConfig) -> str:
        """
        Create a short preview of the mixed audio (first 10 seconds).
        
        Args:
            config: BackgroundMusicConfig with paths and settings
            
        Returns:
            Path to the preview file
        """
        preview_config = BackgroundMusicConfig(
            music_path=config.music_path,
            voice_path=config.voice_path,
            output_path=config.output_path.replace('.wav', '_preview.wav'),
            volume=config.volume,
            fade_in_duration=min(config.fade_in_duration, 1.0),
            fade_out_duration=min(config.fade_out_duration, 1.0)
        )
        
        # Add duration limit to filter
        volume_fraction = config.volume / 100.0
        cmd = [
            'ffmpeg',
            '-i', config.music_path,
            '-i', config.voice_path,
            '-t', '10',  # Limit to 10 seconds
            '-filter_complex',
            self._build_filter_complex(volume_fraction, 1.0, 1.0),
            '-map', '[mixed]',
            '-y',
            preview_config.output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return preview_config.output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Preview generation failed: {e.stderr}")
            raise RuntimeError(f"Preview generation failed: {e.stderr}")


# Singleton instance
background_music_service = BackgroundMusicService()
