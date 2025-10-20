import { useState, useEffect, useRef } from 'react';
import { Player } from './components/Player';
import { ChannelMenu } from './components/ChannelMenu';
import { ManagementView } from './components/ManagementView';
import { useKeyboard } from './hooks/useKeyboard';
import { getNextVideo, skipVideo } from './services/api';
import './App.css';

function App() {
  const [currentVideo, setCurrentVideo] = useState(null);
  const [currentChannel, setCurrentChannel] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [showManagement, setShowManagement] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const appRef = useRef(null);
  const playerRef = useRef(null);

  useEffect(() => {
    if (currentChannel) {
      loadNextVideo();
    }
  }, [currentChannel]);

  const loadNextVideo = async () => {
    if (!currentChannel) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const video = await getNextVideo(currentChannel.id);
      setCurrentVideo(video);
    } catch (err) {
      console.error('Failed to load next video:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = async () => {
    if (!currentChannel || !currentVideo) {
      console.log('Cannot skip: missing channel or video', { currentChannel, currentVideo });
      return;
    }

    console.log('Skipping video:', currentVideo.id, 'on channel:', currentChannel.id);
    setLoading(true);
    setError(null);

    try {
      const nextVideo = await skipVideo(currentChannel.id, currentVideo.id);
      console.log('Next video received:', nextVideo);
      setCurrentVideo(nextVideo);
    } catch (err) {
      console.error('Failed to skip video:', err);
      setError(err.message);
      loadNextVideo();
    } finally {
      setLoading(false);
    }
  };

  const handleVideoEnd = () => {
    console.log('Video ended, loading next...');
    loadNextVideo();
  };

  const handleChannelSelect = (channel) => {
    setCurrentChannel(channel);
    setCurrentVideo(null);
  };

  const handleTogglePlayPause = () => {
    if (playerRef.current) {
      playerRef.current.togglePlay();
    }
  };

  const handleToggleFullscreen = async () => {
    if (showManagement) {
      return;
    }

    try {
      if (!document.fullscreenElement) {
        const target = appRef.current ?? document.documentElement;
        if (target.requestFullscreen) {
          await target.requestFullscreen();
        } else if (target.webkitRequestFullscreen) {
          target.webkitRequestFullscreen();
        }
      } else {
        if (document.exitFullscreen) {
          await document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          document.webkitExitFullscreen();
        }
      }
    } catch (err) {
      console.error('Failed to toggle fullscreen:', err);
    }
  };

  useKeyboard({
    onLeft: () => !showManagement && setMenuOpen(true),
    onRight: handleSkip,
    onSpace: handleTogglePlayPause,
    onEnter: handleToggleFullscreen,
    menuOpen: menuOpen,
  });

  return (
    <div className="app" ref={appRef}>
      {showManagement ? (
        <ManagementView
          onClose={() => {
            setShowManagement(false);
            if (currentChannel) {
              loadNextVideo();
            }
          }}
        />
      ) : (
        <>
          <ChannelMenu
            isOpen={menuOpen}
            onClose={() => setMenuOpen(false)}
            onSelectChannel={handleChannelSelect}
            currentChannelId={currentChannel?.id}
            onManage={() => {
              setMenuOpen(false);
              setShowManagement(true);
            }}
          />

          <div className="player-view">
            {loading && !currentVideo && (
              <div className="loading-overlay">
                <div className="spinner"></div>
                <p>Loading video...</p>
              </div>
            )}

            {error && (
              <div className="error-overlay">
                <div className="error-message">
                  <h3>Error</h3>
                  <p>{error}</p>
                  <button onClick={loadNextVideo} className="primary">
                    Try Again
                  </button>
                </div>
              </div>
            )}

            {!currentChannel && !loading && (
              <div className="welcome-screen">
                <h1>Welcome to OG Media</h1>
                <p>Your lean-back YouTube channel player</p>
                <div className="welcome-actions">
                  <button onClick={() => setMenuOpen(true)} className="primary">
                    Select Channel
                  </button>
                  <button onClick={() => setShowManagement(true)}>
                    Manage Channels
                  </button>
                </div>
                <div className="keyboard-hints">
                  <div className="hint">
                    <kbd>Left Arrow</kbd> <span>Open menu</span>
                  </div>
                  <div className="hint">
                    <kbd>Right Arrow</kbd> <span>Skip video</span>
                  </div>
                  <div className="hint">
                    <kbd>Space</kbd> <span>Play/Pause</span>
                  </div>
                  <div className="hint">
                    <kbd>Enter</kbd> <span>Toggle fullscreen</span>
                  </div>
                </div>
              </div>
            )}

            {currentChannel && !error && (
              <>
                <Player video={currentVideo} onVideoEnd={handleVideoEnd} ref={playerRef} />

                <div className="channel-indicator">
                  <span className="channel-label">Channel:</span>
                  <span className="channel-value">{currentChannel.name}</span>
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default App;
