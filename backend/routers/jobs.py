"""Job queue router for async TTS processing with ARQ."""

import uuid
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Try to import ARQ, fallback to sync processing if not available
try:
    from arq import create_pool
    from arq.connections import RedisSettings
    ARQ_AVAILABLE = True
    # Redis settings (only defined when ARQ is available)
    REDIS_SETTINGS = RedisSettings(host="localhost", port=6379, database=0)
except ImportError:
    ARQ_AVAILABLE = False
    REDIS_SETTINGS = None

from models.database import get_db, Chapter
from sqlmodel import Session

router = APIRouter()


class TTSJobRequest(BaseModel):
    """Request to enqueue a TTS job."""
    chapter_id: str
    voice_id: str
    language: Optional[str] = "en"
    priority: Optional[int] = 5  # 1-10, lower = higher priority


class TTSJobResponse(BaseModel):
    """Response with job details."""
    job_id: str
    chapter_id: str
    status: str
    progress: float
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    estimated_duration: Optional[int] = None  # seconds


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float
    message: str


async def get_redis():
    """Get Redis connection pool."""
    if not ARQ_AVAILABLE:
        raise HTTPException(status_code=503, detail="Job queue not available - ARQ not installed")
    return await create_pool(REDIS_SETTINGS)


def generate_job_id() -> str:
    """Generate unique job ID."""
    return f"tts_{uuid.uuid4().hex[:12]}"


@router.post("/tts/enqueue", response_model=TTSJobResponse)
async def enqueue_tts_job(
    request: TTSJobRequest,
    db: Session = Depends(get_db)
):
    """
    Enqueue a TTS generation job.
    
    Returns immediately with job ID. Use /jobs/{job_id}/status to poll progress.
    """
    # Verify chapter exists
    chapter = db.get(Chapter, request.chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    if not chapter.content:
        raise HTTPException(status_code=400, detail="Chapter has no content to synthesize")
    
    job_id = generate_job_id()
    created_at = datetime.utcnow().isoformat()
    
    # Estimate duration (rough: ~150 chars per second)
    estimated_duration = len(chapter.content) // 150
    
    if ARQ_AVAILABLE:
        try:
            redis = await get_redis()
            
            # Store job metadata in Redis
            await redis.hset(f"tts_job:{job_id}", mapping={
                'job_id': job_id,
                'chapter_id': request.chapter_id,
                'voice_id': request.voice_id,
                'language': request.language or chapter.language,
                'status': 'pending',
                'progress': '0',
                'created_at': created_at,
                'text_length': str(len(chapter.content)),
            })
            
            # Enqueue the job
            await redis.enqueue_job(
                'generate_tts',
                chapter.content,
                request.voice_id,
                request.chapter_id,
                job_id,
                _queue_name='tts',
            )
            
            await redis.close()
            
        except Exception as e:
            # Fallback to sync processing if Redis is down
            raise HTTPException(
                status_code=503, 
                detail=f"Job queue unavailable: {str(e)}. Use /tts/generate for synchronous processing."
            )
    else:
        # ARQ not available, process synchronously
        from services.tts_service import tts_service
        try:
            output_path = tts_service.generate(
                chapter.content, 
                request.voice_id, 
                use_cache=True
            )
            
            return TTSJobResponse(
                job_id=job_id,
                chapter_id=request.chapter_id,
                status="completed",
                progress=100.0,
                output_path=output_path,
                created_at=created_at,
                completed_at=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
    
    return TTSJobResponse(
        job_id=job_id,
        chapter_id=request.chapter_id,
        status="pending",
        progress=0.0,
        created_at=created_at,
        estimated_duration=estimated_duration,
    )


@router.get("/tts/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a TTS job."""
    if not ARQ_AVAILABLE:
        raise HTTPException(status_code=503, detail="Job queue not available")
    
    try:
        redis = await get_redis()
        job_data = await redis.hgetall(f"tts_job:{job_id}")
        await redis.close()
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        status = job_data.get('status', 'unknown')
        progress = float(job_data.get('progress', 0))
        
        messages = {
            'pending': 'Waiting in queue...',
            'processing': f'Generating audio... {progress:.0f}%',
            'completed': 'Audio generation complete!',
            'failed': f'Error: {job_data.get("error_message", "Unknown error")}',
        }
        
        return JobStatusResponse(
            job_id=job_id,
            status=status,
            progress=progress,
            message=messages.get(status, f'Status: {status}'),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/tts/{job_id}/result", response_model=TTSJobResponse)
async def get_job_result(job_id: str):
    """Get the full result of a completed TTS job."""
    if not ARQ_AVAILABLE:
        raise HTTPException(status_code=503, detail="Job queue not available")
    
    try:
        redis = await get_redis()
        job_data = await redis.hgetall(f"tts_job:{job_id}")
        await redis.close()
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return TTSJobResponse(
            job_id=job_id,
            chapter_id=job_data.get('chapter_id', ''),
            status=job_data.get('status', 'unknown'),
            progress=float(job_data.get('progress', 0)),
            output_path=job_data.get('output_path') or None,
            error_message=job_data.get('error_message') or None,
            created_at=job_data.get('created_at', ''),
            completed_at=job_data.get('completed_at') or None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job result: {str(e)}")


@router.post("/tts/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a pending or processing TTS job."""
    if not ARQ_AVAILABLE:
        raise HTTPException(status_code=503, detail="Job queue not available")
    
    try:
        redis = await get_redis()
        
        # Get current status
        job_data = await redis.hgetall(f"tts_job:{job_id}")
        if not job_data:
            await redis.close()
            raise HTTPException(status_code=404, detail="Job not found")
        
        status = job_data.get('status')
        
        if status == 'completed':
            await redis.close()
            raise HTTPException(status_code=400, detail="Cannot cancel completed job")
        
        if status == 'failed':
            await redis.close()
            raise HTTPException(status_code=400, detail="Job already failed")
        
        # Mark as cancelled
        await redis.hset(f"tts_job:{job_id}", mapping={
            'status': 'cancelled',
            'progress': '0',
        })
        
        await redis.close()
        
        return {"success": True, "message": "Job cancelled"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/queue/stats")
async def get_queue_stats():
    """Get job queue statistics."""
    if not ARQ_AVAILABLE:
        return {
            "available": False,
            "message": "ARQ not installed - running in synchronous mode",
        }
    
    try:
        redis = await get_redis()
        
        # Count jobs by status
        pending = 0
        processing = 0
        completed = 0
        failed = 0
        
        # Scan for all job keys
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match="tts_job:*")
            for key in keys:
                job_data = await redis.hgetall(key)
                status = job_data.get('status')
                if status == 'pending':
                    pending += 1
                elif status == 'processing':
                    processing += 1
                elif status == 'completed':
                    completed += 1
                elif status == 'failed':
                    failed += 1
            
            if cursor == 0:
                break
        
        await redis.close()
        
        return {
            "available": True,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "total": pending + processing + completed + failed,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {str(e)}")
