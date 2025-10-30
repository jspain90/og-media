from sqlalchemy.orm import Session
from app.models import Channel, Source, VideoQueue
from app.services.youtube import youtube_service
import random
from typing import List, Dict, Optional
from datetime import datetime, timezone

class QueueBuilder:
    """Service for building and managing video queues for channels"""

    def __init__(self, db: Session):
        self.db = db

    def rebuild_channel_queue(self, channel_id: int) -> int:
        """
        Rebuild the video queue for a channel by fetching from all its sources
        and ordering them according to the channel's playback settings.

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

        # Collect videos per source
        videos_by_source: List[List[Dict]] = []

        for source in sources:
            try:
                if source.source_type == 'channel':
                    videos = youtube_service.get_channel_videos(source.youtube_id)
                elif source.source_type == 'playlist':
                    videos = youtube_service.get_playlist_videos(source.youtube_id)
                else:
                    continue

                if videos:
                    videos_by_source.append(videos)
                print(f"Fetched {len(videos)} videos from {source.source_type} {source.youtube_id}")

            except Exception as e:
                print(f"Error fetching videos from source {source.id}: {e}")
                continue

        if not videos_by_source:
            print(f"No videos fetched for channel {channel_id}")
            return 0

        play_order = getattr(channel, "play_order", "random") or "random"
        if play_order not in {"random", "chronological_newest", "chronological_oldest"}:
            play_order = "random"
        if play_order == "random":
            collected: List[Dict] = []
            for video_list in videos_by_source:
                collected.extend(video_list)
            random.shuffle(collected)
            ordered_videos = self._dedupe_preserve_order(collected)
        else:
            newest_first = play_order == "chronological_newest"
            ordered_videos = self._build_round_robin_by_date(videos_by_source, newest_first)

        if not ordered_videos:
            print(f"No videos available after ordering for channel {channel_id}")
            return 0

        # Clear existing queue for this channel
        self.db.query(VideoQueue).filter(VideoQueue.channel_id == channel_id).delete()

        # Add videos to queue
        for position, video in enumerate(ordered_videos):
            published_at = self._parse_published_at(video.get('published_at'))
            queue_item = VideoQueue(
                channel_id=channel_id,
                video_id=video['video_id'],
                video_url=video['video_url'],
                title=video['title'],
                thumbnail_url=video['thumbnail_url'],
                channel_name=video['channel_name'],
                published_at=published_at,
                position=position,
                played=False
            )
            self.db.add(queue_item)

        self.db.commit()
        print(f"Added {len(ordered_videos)} videos to queue for channel {channel_id}")
        return len(ordered_videos)

    def _dedupe_preserve_order(self, videos: List[Dict]) -> List[Dict]:
        """Remove duplicate video IDs while preserving order"""
        seen = set()
        unique: List[Dict] = []
        for video in videos:
            video_id = video.get("video_id")
            if not video_id or video_id in seen:
                continue
            seen.add(video_id)
            unique.append(video)
        return unique

    def _build_round_robin_by_date(self, videos_by_source: List[List[Dict]], newest_first: bool) -> List[Dict]:
        """Interleave sources while respecting upload chronology per source"""
        ordered_sources: List[List[Dict]] = []
        for videos in videos_by_source:
            if not videos:
                continue
            ordered = sorted(
                videos,
                key=lambda v: self._sort_key_for_date(v.get("published_at"), newest_first),
                reverse=newest_first,
            )
            ordered_sources.append(ordered)

        result: List[Dict] = []
        seen = set()

        while True:
            active_indexes = [idx for idx, items in enumerate(ordered_sources) if items]
            if not active_indexes:
                break

            random.shuffle(active_indexes)
            progress = False

            for idx in active_indexes:
                queue = ordered_sources[idx]
                while queue:
                    video = queue.pop(0)
                    video_id = video.get("video_id")
                    if not video_id or video_id in seen:
                        continue
                    seen.add(video_id)
                    result.append(video)
                    progress = True
                    break

            if not progress:
                break

        return result

    def _parse_published_at(self, value: Optional[str]) -> Optional[datetime]:
        """Convert ISO 8601 timestamp string to naive UTC datetime"""
        if not value:
            return None
        try:
            normalized = value.replace('Z', '+00:00')
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is not None:
                return parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except Exception:
            return None

    def _sort_key_for_date(self, value: Optional[str], newest_first: bool) -> datetime:
        """Provide a stable sort key for published_at values"""
        parsed = self._parse_published_at(value)
        if parsed:
            return parsed
        return datetime.min if newest_first else datetime.max

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

