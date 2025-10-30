from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from app.database import get_db
from app.models import Channel
from app.services.queue_builder import QueueBuilder

router = APIRouter(prefix="/api/channels", tags=["channels"])

# Pydantic schemas
class PlayOrder(str, Enum):
    RANDOM = "random"
    CHRONOLOGICAL_NEWEST = "chronological_newest"
    CHRONOLOGICAL_OLDEST = "chronological_oldest"

class ChannelCreate(BaseModel):
    name: str
    play_order: PlayOrder = PlayOrder.RANDOM

class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    play_order: Optional[PlayOrder] = None

class ChannelResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    play_order: PlayOrder

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ChannelResponse])
def get_channels(db: Session = Depends(get_db)):
    """Get all channels"""
    channels = db.query(Channel).order_by(Channel.name).all()
    return channels

@router.get("/{channel_id}", response_model=ChannelResponse)
def get_channel(channel_id: int, db: Session = Depends(get_db)):
    """Get a specific channel by ID"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.post("/", response_model=ChannelResponse, status_code=201)
def create_channel(channel_data: ChannelCreate, db: Session = Depends(get_db)):
    """Create a new channel"""
    # Check if channel with this name already exists
    existing = db.query(Channel).filter(Channel.name == channel_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Channel with this name already exists")

    channel = Channel(
        name=channel_data.name,
        play_order=channel_data.play_order.value,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel

@router.put("/{channel_id}", response_model=ChannelResponse)
def update_channel(channel_id: int, channel_data: ChannelUpdate, db: Session = Depends(get_db)):
    """Update channel properties"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    updates = channel_data.model_dump(exclude_none=True)
    if not updates:
        return channel

    if "name" in updates:
        new_name = updates["name"]
        existing = db.query(Channel).filter(
            Channel.name == new_name,
            Channel.id != channel_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Another channel with this name already exists")
        channel.name = new_name

    play_order_changed = False
    if "play_order" in updates:
        channel.play_order = channel_data.play_order.value
        play_order_changed = True

    db.commit()
    db.refresh(channel)

    if play_order_changed:
        try:
            queue_builder = QueueBuilder(db)
            queue_builder.rebuild_channel_queue(channel_id)
        except Exception as exc:
            print(f"Failed to rebuild queue after play order change for channel {channel_id}: {exc}")

    return channel

@router.delete("/{channel_id}", status_code=204)
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    """Delete a channel (and all its sources and queue)"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    db.delete(channel)
    db.commit()
    return None



