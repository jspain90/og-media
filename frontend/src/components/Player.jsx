import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import { useYouTubePlayer } from '../hooks/useYouTubePlayer';
import './Player.css';

export const Player = forwardRef(({ video, onVideoEnd }, ref) => {
  const { containerRef, isPlaying, togglePlay } = useYouTubePlayer({
    videoId: video?.video_id,
    onEnd: onVideoEnd,
  });
  const wrapperRef = useRef(null);

  // Expose togglePlay to parent component
  useImperativeHandle(ref, () => ({
    togglePlay,
  }));

  // Keep focus on the custom wrapper so keyboard controls keep working
  useEffect(() => {
    if (video && wrapperRef.current) {
      wrapperRef.current.focus({ preventScroll: true });
    }
  }, [video?.video_id]);

  const focusWrapper = () => {
    if (wrapperRef.current) {
      wrapperRef.current.focus({ preventScroll: true });
    }
  };

  const handleOverlayClick = (event) => {
    event.preventDefault();
    event.stopPropagation();
    focusWrapper();
    togglePlay();
  };

  const handleOverlayTouchEnd = (event) => {
    event.preventDefault();
    event.stopPropagation();
    focusWrapper();
    togglePlay();
  };

  if (!video) {
    return (
      <div className="player-container">
        <div className="no-video">
          <h2>No video to play</h2>
          <p>Select a channel or add sources to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="player-container">
      <div
        className="player-wrapper"
        ref={wrapperRef}
        tabIndex={-1}
      >
        <div ref={containerRef} className="youtube-player" />
        <div
          className="player-overlay"
          role="button"
          aria-label="Toggle playback"
          onMouseDown={(event) => {
            event.preventDefault();
            focusWrapper();
          }}
          onClick={handleOverlayClick}
          onTouchEnd={handleOverlayTouchEnd}
        />
      </div>

      {/* Video info overlay */}
      <div className="video-info">
        <h3 className="video-title">{video.title}</h3>
        {video.channel_name && (
          <p className="video-channel">{video.channel_name}</p>
        )}
      </div>

      {/* Play/pause indicator */}
      {!isPlaying && (
        <div className="pause-indicator">
          <div className="pause-icon">❚❚</div>
        </div>
      )}
    </div>
  );
});
