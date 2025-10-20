from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Source, Channel
from app.services.youtube import youtube_service

router = APIRouter(prefix="/api/sources", tags=["sources"])

# Pydantic schemas
class SourceCreate(BaseModel):
    channel_id: int
    youtube_id: str
    source_type: str  # 'channel' or 'playlist'
    name: str | None = None

class SourceResponse(BaseModel):
    id: int
    channel_id: int
    youtube_id: str
    source_type: str
    name: str | None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[SourceResponse])
def get_sources(channel_id: int | None = None, db: Session = Depends(get_db)):
    """Get all sources, optionally filtered by channel_id"""
    query = db.query(Source)
    if channel_id:
        query = query.filter(Source.channel_id == channel_id)
    sources = query.order_by(Source.created_at).all()
    return sources

@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):
    """Get a specific source by ID"""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source

@router.post("/", response_model=SourceResponse, status_code=201)
def create_source(source_data: SourceCreate, db: Session = Depends(get_db)):
    """Create a new source for a channel"""
    # Validate channel exists
    channel = db.query(Channel).filter(Channel.id == source_data.channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Validate source_type
    if source_data.source_type not in ['channel', 'playlist']:
        raise HTTPException(status_code=400, detail="source_type must be 'channel' or 'playlist'")

    # Resolve channel handle/URL to channel ID if source_type is 'channel'
    resolved_id = source_data.youtube_id
    friendly_name = source_data.name

    if source_data.source_type == 'channel':
        # Try to resolve handle to channel ID
        channel_id_resolved, channel_name = youtube_service.resolve_channel_id(source_data.youtube_id)

        if channel_id_resolved:
            resolved_id = channel_id_resolved
            # If user didn't provide a name, use the channel name from YouTube
            if not friendly_name:
                friendly_name = channel_name
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Could not resolve channel: '{source_data.youtube_id}'. Please provide a valid channel ID, handle (@name), or URL."
            )

    # Check for duplicate youtube_id in the same channel
    existing = db.query(Source).filter(
        Source.channel_id == source_data.channel_id,
        Source.youtube_id == resolved_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="This YouTube source is already added to this channel")

    source = Source(
        channel_id=source_data.channel_id,
        youtube_id=resolved_id,
        source_type=source_data.source_type,
        name=friendly_name
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

@router.put("/{source_id}", response_model=SourceResponse)
def update_source(source_id: int, source_data: SourceCreate, db: Session = Depends(get_db)):
    """Update a source"""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Validate source_type
    if source_data.source_type not in ['channel', 'playlist']:
        raise HTTPException(status_code=400, detail="source_type must be 'channel' or 'playlist'")

    source.youtube_id = source_data.youtube_id
    source.source_type = source_data.source_type
    source.name = source_data.name
    db.commit()
    db.refresh(source)
    return source

@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """Delete a source"""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(source)
    db.commit()
    return None
