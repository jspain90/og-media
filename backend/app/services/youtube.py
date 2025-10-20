from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import os
import re
from typing import List, Dict, Optional, Tuple

load_dotenv()

class YouTubeService:
    """Service for interacting with YouTube Data API v3"""

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY not found in environment variables")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.max_results = int(os.getenv("VIDEOS_PER_SOURCE", 50))
        self.max_fetch_limit = int(os.getenv("MAX_FETCH_PER_SOURCE", 500))

    def get_channel_videos(self, channel_id: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        Fetch videos from a YouTube channel

        Args:
            channel_id: YouTube channel ID (e.g., 'UC_x5XG1OV2P6uZZ5FSM9Ttw')
            max_results: Number of videos to fetch (default from env)

        Returns:
            List of video dictionaries with id, title, thumbnail, etc.
        """
        max_results = max_results or self.max_results
        videos = []

        try:
            # First, get the uploads playlist ID for the channel
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()

            if not channel_response.get('items'):
                return []

            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # Fetch videos from the uploads playlist
            videos = self._get_playlist_videos(uploads_playlist_id, max_results)

        except HttpError as e:
            print(f"YouTube API error fetching channel {channel_id}: {e}")

        return videos

    def get_playlist_videos(self, playlist_id: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        Fetch videos from a YouTube playlist

        Args:
            playlist_id: YouTube playlist ID
            max_results: Number of videos to fetch (default from env)

        Returns:
            List of video dictionaries
        """
        max_results = max_results or self.max_results
        return self._get_playlist_videos(playlist_id, max_results)

    def _get_playlist_videos(self, playlist_id: str, max_results: int) -> List[Dict]:
        """
        Internal method to fetch videos from a playlist.

        Implements smart incremental fetching: fetches until we have max_results
        FILTERED videos (after removing Shorts), up to a safety limit.

        Args:
            playlist_id: YouTube playlist ID
            max_results: Target number of FILTERED videos to return

        Returns:
            List of filtered video dictionaries
        """
        filtered_videos = []
        next_page_token = None
        total_raw_fetched = 0

        try:
            while len(filtered_videos) < max_results and total_raw_fetched < self.max_fetch_limit:
                # Fetch one page of videos (up to 50 at a time)
                request = self.youtube.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=playlist_id,
                    maxResults=50,  # Always fetch full page for efficiency
                    pageToken=next_page_token
                )
                response = request.execute()

                # Collect raw videos from this batch
                batch_videos = []
                for item in response.get('items', []):
                    snippet = item['snippet']

                    # Skip private/deleted videos
                    if snippet['title'] == 'Private video' or snippet['title'] == 'Deleted video':
                        continue

                    video_data = {
                        'video_id': snippet['resourceId']['videoId'],
                        'video_url': f"https://www.youtube.com/watch?v={snippet['resourceId']['videoId']}",
                        'title': snippet['title'],
                        'thumbnail_url': snippet['thumbnails'].get('medium', {}).get('url', ''),
                        'channel_name': snippet['videoOwnerChannelTitle'],
                        'published_at': snippet['publishedAt']
                    }
                    batch_videos.append(video_data)

                total_raw_fetched += len(batch_videos)

                # Filter this batch immediately
                batch_filtered = self._filter_shorts(batch_videos)
                filtered_videos.extend(batch_filtered)

                # Check if we have enough filtered videos
                if len(filtered_videos) >= max_results:
                    break

                # Check if there are more pages
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    # No more videos available
                    break

        except HttpError as e:
            print(f"YouTube API error fetching playlist {playlist_id}: {e}")

        # Log the fetching results
        print(f"Fetched {total_raw_fetched} raw videos, kept {len(filtered_videos)} after filtering")

        # Return only up to max_results (in case we went over)
        return filtered_videos[:max_results]

    def _filter_shorts(self, videos: List[Dict]) -> List[Dict]:
        """Filter out YouTube Shorts (videos <= 180 seconds / 3 minutes)"""
        if not videos:
            return videos

        # Get video IDs
        video_ids = [v['video_id'] for v in videos]

        # Fetch video details to get durations
        try:
            # Process in chunks of 50 (API limit)
            durations = {}
            for i in range(0, len(video_ids), 50):
                chunk = video_ids[i:i+50]
                request = self.youtube.videos().list(
                    part='contentDetails',
                    id=','.join(chunk)
                )
                response = request.execute()

                for item in response.get('items', []):
                    video_id = item['id']
                    duration_iso = item['contentDetails']['duration']
                    # Convert ISO 8601 duration to seconds
                    duration_seconds = self._parse_duration(duration_iso)
                    durations[video_id] = duration_seconds

            # Filter out videos that are 180 seconds or less (Shorts)
            filtered_videos = [
                v for v in videos
                if durations.get(v['video_id'], 0) > 180
            ]

            shorts_count = len(videos) - len(filtered_videos)
            if shorts_count > 0:
                # Avoid non-ASCII symbols so Windows console encoding won't fail.
                print(f"Filtered out {shorts_count} Shorts (<=3min)")

            return filtered_videos

        except HttpError as e:
            print(f"YouTube API error filtering Shorts: {e}")
            # If we can't fetch durations, return all videos
            return videos

    def _parse_duration(self, duration_iso: str) -> int:
        """
        Parse ISO 8601 duration string to seconds
        Example: PT1M30S = 90 seconds, PT15S = 15 seconds
        """
        import re

        # Pattern: PT(hours)H(minutes)M(seconds)S
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_iso)

        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    def get_video_details(self, video_ids: List[str]) -> Dict[str, Dict]:
        """
        Fetch detailed information for specific video IDs

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            Dictionary mapping video_id to video details (including duration)
        """
        if not video_ids:
            return {}

        details = {}

        try:
            # API allows up to 50 IDs per request
            for i in range(0, len(video_ids), 50):
                chunk = video_ids[i:i+50]
                request = self.youtube.videos().list(
                    part='contentDetails,snippet',
                    id=','.join(chunk)
                )
                response = request.execute()

                for item in response.get('items', []):
                    video_id = item['id']
                    details[video_id] = {
                        'duration': item['contentDetails']['duration'],
                        'title': item['snippet']['title'],
                        'channel_name': item['snippet']['channelTitle']
                    }

        except HttpError as e:
            print(f"YouTube API error fetching video details: {e}")

        return details

    def resolve_channel_id(self, user_input: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Resolve various YouTube channel input formats to a channel ID.
        Accepts: channel IDs, handles (@username), URLs, custom URLs

        Args:
            user_input: Channel ID, handle (@name), or URL

        Returns:
            Tuple of (channel_id, friendly_name) or (None, None) if not found
        """
        user_input = user_input.strip()

        # If it's already a valid channel ID (starts with UC and alphanumeric)
        if re.match(r'^UC[\w-]{22}$', user_input):
            return (user_input, None)

        # Extract handle from various URL formats
        handle = None

        # Pattern: @username (with or without @)
        if user_input.startswith('@'):
            handle = user_input[1:]  # Remove @
        elif re.match(r'^[\w-]+$', user_input) and not user_input.startswith('UC'):
            # Plain username without @
            handle = user_input
        else:
            # Try to extract from URLs
            # Pattern: youtube.com/@username or youtube.com/c/username or youtube.com/user/username
            url_patterns = [
                r'youtube\.com/@([\w-]+)',
                r'youtube\.com/c/([\w-]+)',
                r'youtube\.com/user/([\w-]+)',
                r'youtube\.com/channel/(UC[\w-]{22})',  # Direct channel ID in URL
            ]

            for pattern in url_patterns:
                match = re.search(pattern, user_input)
                if match:
                    extracted = match.group(1)
                    # If we extracted a channel ID directly
                    if extracted.startswith('UC'):
                        return (extracted, None)
                    handle = extracted
                    break

        # If we have a handle, resolve it via API
        if handle:
            try:
                # Try using forUsername first (for legacy custom URLs)
                try:
                    request = self.youtube.channels().list(
                        part='snippet',
                        forUsername=handle
                    )
                    response = request.execute()

                    if response.get('items'):
                        channel = response['items'][0]
                        channel_id = channel['id']
                        channel_name = channel['snippet']['title']
                        return (channel_id, channel_name)
                except:
                    pass  # forUsername didn't work, try search

                # Use search API to find channel by handle/name
                search_request = self.youtube.search().list(
                    part='snippet',
                    q=handle,
                    type='channel',
                    maxResults=5
                )
                search_response = search_request.execute()

                if search_response.get('items'):
                    # Look for exact match or best match
                    for item in search_response['items']:
                        channel_title = item['snippet']['channelTitle']
                        # Check if this is a close match (case-insensitive)
                        if handle.lower() in channel_title.lower() or channel_title.lower() in handle.lower():
                            channel_id = item['snippet']['channelId']
                            channel_name = channel_title
                            return (channel_id, channel_name)

                    # If no close match, return the first result
                    first_result = search_response['items'][0]
                    channel_id = first_result['snippet']['channelId']
                    channel_name = first_result['snippet']['channelTitle']
                    print(f"Found channel '{channel_name}' for handle '{handle}'")
                    return (channel_id, channel_name)
                else:
                    print(f"No channel found for handle: {handle}")
                    return (None, None)

            except HttpError as e:
                print(f"YouTube API error resolving handle '{handle}': {e}")
                return (None, None)

        # Couldn't parse the input
        print(f"Could not parse channel input: {user_input}")
        return (None, None)

# Singleton instance
youtube_service = YouTubeService()
