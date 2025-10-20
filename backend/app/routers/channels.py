from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Channel

router = APIRouter(prefix="/api/channels", tags=["channels"])

# Pydantic schemas
class ChannelCreate(BaseModel):
    name: str

class ChannelResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

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

    channel = Channel(name=channel_data.name)
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel

@router.put("/{channel_id}", response_model=ChannelResponse)
def update_channel(channel_id: int, channel_data: ChannelCreate, db: Session = Depends(get_db)):
    """Update a channel's name"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Check if new name conflicts with another channel
    existing = db.query(Channel).filter(
        Channel.name == channel_data.name,
        Channel.id != channel_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Another channel with this name already exists")

    channel.name = channel_data.name
    db.commit()
    db.refresh(channel)
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
