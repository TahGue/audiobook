"""ARQ Worker for async TTS job processing."""

import os
import asyncio
from typing import Dict, Any
from arq import create_pool
from arq.connections import RedisSettings
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib

# Import services
from services.tts_service import tts_service, TTSEngine


@dataclass
class TTSJob:
    """TTS job configuration."""
    job_id: str
    text: str
    voice_id: str
    language: str
    chapter_id: str
    status: str = "pending"  # pending, processing, completed, failed
    progress: float = 0.0
    output_path: str = ""
    error_message: str = ""
    created_at: str = ""
    completed_at: str = ""


# Redis settings (can use embedded Redis for local-first)
REDIS_SETTINGS = RedisSettings(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    database=int(os.getenv("REDIS_DB", 0)),
    password=os.getenv("REDIS_PASSWORD") or None,
)


async def generate_tts(ctx, text: str, voice_id: str, chapter_id: str, job_id: str) -> Dict[str, Any]:
    """
    Background task to generate TTS audio.
    
    Args:
        ctx: ARQ context
        text: Text to synthesize
        voice_id: Voice identifier
        chapter_id: Chapter ID for reference
        job_id: Unique job identifier
    
    Returns:
        Dictionary with job result
    """
    redis = ctx['redis']
    
    try:
        # Update status to processing
        await redis.hset(f"tts_job:{job_id}", mapping={
            'status': 'processing',
            'progress': '10',
        })
        
        # Generate audio using TTS service
        output_path = tts_service.generate(text, voice_id, use_cache=True)
        
        # Update progress
        await redis.hset(f"tts_job:{job_id}", mapping={
            'progress': '80',
        })
        
        # Get audio duration (optional enhancement)
        duration = 0
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(output_path)
            duration = len(audio) / 1000  # Convert to seconds
        except:
            pass
        
        # Mark as completed
        completed_at = datetime.utcnow().isoformat()
        await redis.hset(f"tts_job:{job_id}", mapping={
            'status': 'completed',
            'progress': '100',
            'output_path': output_path,
            'duration': str(duration),
            'completed_at': completed_at,
        })
        
        return {
            'success': True,
            'job_id': job_id,
            'output_path': output_path,
            'duration': duration,
        }
        
    except Exception as e:
        error_msg = str(e)
        await redis.hset(f"tts_job:{job_id}", mapping={
            'status': 'failed',
            'error_message': error_msg,
            'progress': '0',
        })
        
        return {
            'success': False,
            'job_id': job_id,
            'error': error_msg,
        }


async def startup(ctx):
    """Worker startup function."""
    print(f"ARQ Worker started at {datetime.utcnow().isoformat()}")
    ctx['redis'] = await create_pool(REDIS_SETTINGS)


async def shutdown(ctx):
    """Worker shutdown function."""
    print(f"ARQ Worker stopped at {datetime.utcnow().isoformat()}")
    await ctx['redis'].close()


# ARQ worker configuration
class WorkerSettings:
    """ARQ worker settings."""
    functions = [generate_tts]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = REDIS_SETTINGS
    max_jobs = 10  # Concurrent jobs
    job_timeout = 300  # 5 minutes timeout
    keep_result = 3600  # Keep results for 1 hour
    poll_delay = 1.0  # Poll interval


# For running: arq worker.WorkerSettings
