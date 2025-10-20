import { useEffect, useRef, useState } from 'react';

/**
 * Hook for managing YouTube IFrame Player API
 *
 * @param {Object} options
 * @param {string} options.videoId - YouTube video ID
 * @param {Function} options.onEnd - Called when video ends
 * @param {Function} options.onReady - Called when player is ready
 */
export function useYouTubePlayer({ videoId, onEnd, onReady }) {
  const playerRef = useRef(null);
  const containerRef = useRef(null);
  const [isReady, setIsReady] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  // Load YouTube IFrame API
  useEffect(() => {
    // Check if API already loaded
    if (window.YT && window.YT.Player) {
      return;
    }

    // Load the IFrame Player API code asynchronously
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    const firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

    // API will call this function when ready
    window.onYouTubeIframeAPIReady = () => {
      console.log('YouTube IFrame API ready');
    };
  }, []);

  // Initialize player when container and videoId are ready
  useEffect(() => {
    if (!containerRef.current || !videoId) return;
    if (!window.YT || !window.YT.Player) return;

    // Destroy existing player first
    if (playerRef.current) {
      try {
        playerRef.current.destroy();
      } catch (e) {
        console.warn('Error destroying player:', e);
      }
      playerRef.current = null;
    }

    // Clear container and create placeholder div for YouTube
    const container = containerRef.current;
    container.innerHTML = '';
    const playerDiv = document.createElement('div');
    playerDiv.id = `youtube-player-${Date.now()}`;
    container.appendChild(playerDiv);

    // Create new player using the placeholder div ID
    playerRef.current = new window.YT.Player(playerDiv.id, {
      videoId: videoId,
      playerVars: {
        autoplay: 1,
        controls: 0, // Hide YouTube controls
        disablekb: 1, // Disable keyboard controls on the player
        modestbranding: 1,
        rel: 0,
        showinfo: 0,
        fs: 0, // Disable fullscreen (we control everything)
        iv_load_policy: 3, // Hide annotations
      },
      events: {
        onReady: (event) => {
          console.log('Player ready');
          setIsReady(true);
          if (onReady) onReady(event);
          event.target.playVideo();
        },
        onStateChange: (event) => {
          const state = event.data;
          // -1 (unstarted), 0 (ended), 1 (playing), 2 (paused), 3 (buffering), 5 (video cued)
          if (state === window.YT.PlayerState.PLAYING) {
            setIsPlaying(true);
          } else if (state === window.YT.PlayerState.PAUSED) {
            setIsPlaying(false);
          } else if (state === window.YT.PlayerState.ENDED) {
            setIsPlaying(false);
            if (onEnd) onEnd();
          }
        },
        onError: (event) => {
          console.error('YouTube player error:', event.data);
          // Error codes: 2 (invalid param), 5 (HTML5 error), 100 (video not found), 101/150 (embedding not allowed)
          if (onEnd) onEnd(); // Skip to next video on error
        },
      },
    });

    return () => {
      if (playerRef.current) {
        try {
          playerRef.current.destroy();
        } catch (e) {
          console.warn('Error destroying player on cleanup:', e);
        }
        playerRef.current = null;
      }
    };
  }, [videoId, onEnd, onReady]);

  // Player control functions
  const play = () => {
    if (playerRef.current && isReady) {
      playerRef.current.playVideo();
    }
  };

  const pause = () => {
    if (playerRef.current && isReady) {
      playerRef.current.pauseVideo();
    }
  };

  const togglePlay = () => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  };

  return {
    containerRef,
    playerRef,
    isReady,
    isPlaying,
    play,
    pause,
    togglePlay,
  };
}
