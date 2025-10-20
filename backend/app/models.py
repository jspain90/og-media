from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Channel(Base):
    """A user-defined channel (e.g., 'Art Tutorials', 'Coding Talks')"""
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sources = relationship("Source", back_populates="channel", cascade="all, delete-orphan")
    videos = relationship("VideoQueue", back_populates="channel", cascade="all, delete-orphan")

class Source(Base):
    """A YouTube channel or playlist that feeds into a Channel"""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    youtube_id = Column(String, nullable=False)  # Channel ID or Playlist ID
    source_type = Column(String, nullable=False)  # 'channel' or 'playlist'
    name = Column(String, nullable=True)  # Optional friendly name
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    channel = relationship("Channel", back_populates="sources")

class VideoQueue(Base):
    """The randomized queue of videos for each channel"""
    __tablename__ = "video_queue"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    video_id = Column(String, nullable=False)  # YouTube video ID
    video_url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    channel_name = Column(String, nullable=True)  # Original YouTube channel name
    duration = Column(String, nullable=True)  # Duration in ISO 8601 format
    position = Column(Integer, nullable=False)  # Position in queue (0-indexed)
    played = Column(Boolean, default=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    channel = relationship("Channel", back_populates="videos")
