from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.services.queue_builder import QueueBuilder
from app.models import Channel

router = APIRouter(prefix="/api/player", tags=["player"])

class VideoResponse(BaseModel):
    id: int
    video_id: str
    video_url: str
    title: str
    thumbnail_url: str | None
    channel_name: str | None
    position: int
    published_at: datetime | None

    class Config:
        from_attributes = True

class QueueStatusResponse(BaseModel):
    total: int
    played: int
    remaining: int

class RebuildResponse(BaseModel):
    channel_id: int
    videos_added: int
    message: str

@router.get("/play/{channel_id}", response_model=VideoResponse)
def get_next_video(channel_id: int, db: Session = Depends(get_db)):
    """
    Get the next video to play for a channel.
    If queue is empty or all videos played, will attempt to rebuild queue first.
    """
    # Verify channel exists
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    queue_builder = QueueBuilder(db)

    # Get next video
    video = queue_builder.get_next_video(channel_id)

    # If no video found, try rebuilding queue
    if not video:
        print(f"Queue empty for channel {channel_id}, rebuilding...")
        count = queue_builder.rebuild_channel_queue(channel_id)

        if count == 0:
            raise HTTPException(
                status_code=404,
                detail="No videos available. Please add sources to this channel."
            )

        video = queue_builder.get_next_video(channel_id)

    if not video:
        raise HTTPException(status_code=404, detail="No videos available in queue")

    return video

class SkipRequest(BaseModel):
    current_video_id: int

@router.post("/skip/{channel_id}", response_model=VideoResponse)
def skip_video(channel_id: int, request: SkipRequest, db: Session = Depends(get_db)):
    """
    Mark current video as played and get the next video
    """
    queue_builder = QueueBuilder(db)

    # Mark current video as played
    queue_builder.mark_video_played(request.current_video_id)

    # Get next video (will rebuild if needed)
    return get_next_video(channel_id, db)

@router.get("/status/{channel_id}", response_model=QueueStatusResponse)
def get_queue_status(channel_id: int, db: Session = Depends(get_db)):
    """Get the status of a channel's queue"""
    # Verify channel exists
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    queue_builder = QueueBuilder(db)
    status = queue_builder.get_queue_status(channel_id)
    return status

@router.post("/rebuild/{channel_id}", response_model=RebuildResponse)
def rebuild_queue(channel_id: int, db: Session = Depends(get_db)):
    """Manually trigger a queue rebuild for a channel"""
    # Verify channel exists
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    queue_builder = QueueBuilder(db)

    try:
        count = queue_builder.rebuild_channel_queue(channel_id)
        return {
            "channel_id": channel_id,
            "videos_added": count,
            "message": f"Successfully rebuilt queue with {count} videos"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebuilding queue: {str(e)}")

@router.post("/rebuild-all")
def rebuild_all_queues(db: Session = Depends(get_db)):
    """Rebuild queues for all channels (used by scheduler)"""
    queue_builder = QueueBuilder(db)

    try:
        results = queue_builder.rebuild_all_queues()
        return {
            "message": "Rebuilt queues for all channels",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebuilding queues: {str(e)}")
