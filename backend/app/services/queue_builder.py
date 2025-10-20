from sqlalchemy.orm import Session
from app.models import Channel, Source, VideoQueue
from app.services.youtube import youtube_service
import random
from typing import List, Dict

class QueueBuilder:
    """Service for building and managing video queues for channels"""

    def __init__(self, db: Session):
        self.db = db

    def rebuild_channel_queue(self, channel_id: int) -> int:
        """
        Rebuild the video queue for a channel by fetching from all its sources
        and randomizing the order.

        Args:
            channel_id: The channel ID to rebuild queue for

        Returns:
            Number of videos added to queue
        """
        # Get the channel
        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")

        # Get all sources for this channel
        sources = self.db.query(Source).filter(Source.channel_id == channel_id).all()

        if not sources:
            print(f"No sources found for channel {channel_id}")
            return 0

        # Collect all videos from all sources
        all_videos = []

        for source in sources:
            try:
                if source.source_type == 'channel':
                    videos = youtube_service.get_channel_videos(source.youtube_id)
                elif source.source_type == 'playlist':
                    videos = youtube_service.get_playlist_videos(source.youtube_id)
                else:
                    continue

                all_videos.extend(videos)
                print(f"Fetched {len(videos)} videos from {source.source_type} {source.youtube_id}")

            except Exception as e:
                print(f"Error fetching videos from source {source.id}: {e}")
                continue

        if not all_videos:
            print(f"No videos fetched for channel {channel_id}")
            return 0

        # Remove duplicates (same video_id)
        unique_videos = {v['video_id']: v for v in all_videos}
        all_videos = list(unique_videos.values())

        # Randomize the order
        random.shuffle(all_videos)

        # Clear existing queue for this channel
        self.db.query(VideoQueue).filter(VideoQueue.channel_id == channel_id).delete()

        # Add videos to queue
        for position, video in enumerate(all_videos):
            queue_item = VideoQueue(
                channel_id=channel_id,
                video_id=video['video_id'],
                video_url=video['video_url'],
                title=video['title'],
                thumbnail_url=video['thumbnail_url'],
                channel_name=video['channel_name'],
                position=position,
                played=False
            )
            self.db.add(queue_item)

        self.db.commit()
        print(f"Added {len(all_videos)} videos to queue for channel {channel_id}")
        return len(all_videos)

    def rebuild_all_queues(self) -> Dict[int, int]:
        """
        Rebuild queues for all channels

        Returns:
            Dictionary mapping channel_id to number of videos added
        """
        channels = self.db.query(Channel).all()
        results = {}

        for channel in channels:
            try:
                count = self.rebuild_channel_queue(channel.id)
                results[channel.id] = count
            except Exception as e:
                print(f"Error rebuilding queue for channel {channel.id}: {e}")
                results[channel.id] = 0

        return results

    def get_next_video(self, channel_id: int) -> VideoQueue | None:
        """
        Get the next unplayed video in the queue for a channel

        Args:
            channel_id: The channel ID

        Returns:
            Next unplayed VideoQueue item, or None if queue is empty/all played
        """
        video = self.db.query(VideoQueue).filter(
            VideoQueue.channel_id == channel_id,
            VideoQueue.played == False
        ).order_by(VideoQueue.position).first()

        return video

    def mark_video_played(self, video_id: int):
        """Mark a video in the queue as played"""
        video = self.db.query(VideoQueue).filter(VideoQueue.id == video_id).first()
        if video:
            video.played = True
            self.db.commit()

    def get_queue_status(self, channel_id: int) -> Dict:
        """
        Get status of a channel's queue

        Returns:
            Dictionary with total, played, and remaining counts
        """
        total = self.db.query(VideoQueue).filter(VideoQueue.channel_id == channel_id).count()
        played = self.db.query(VideoQueue).filter(
            VideoQueue.channel_id == channel_id,
            VideoQueue.played == True
        ).count()

        return {
            'total': total,
            'played': played,
            'remaining': total - played
        }
