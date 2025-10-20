import { useState, useEffect, useRef } from 'react';
import { getChannels } from '../services/api';
import './ChannelMenu.css';

export function ChannelMenu({ isOpen, onClose, onSelectChannel, currentChannelId, onManage }) {
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const channelRefs = useRef([]);

  useEffect(() => {
    if (isOpen) {
      loadChannels();
    }
  }, [isOpen]);

  // Set initial highlighted index when menu opens or channels change
  useEffect(() => {
    if (isOpen && channels.length > 0) {
      // Find the index of the currently playing channel, or default to 0
      const currentIndex = channels.findIndex(ch => ch.id === currentChannelId);
      setHighlightedIndex(currentIndex >= 0 ? currentIndex : 0);
    }
  }, [isOpen, channels, currentChannelId]);

  // Scroll highlighted item into view
  useEffect(() => {
    if (isOpen && channelRefs.current[highlightedIndex]) {
      channelRefs.current[highlightedIndex].scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [highlightedIndex, isOpen]);

  const loadChannels = async () => {
    setLoading(true);
    try {
      const data = await getChannels();
      setChannels(data);
    } catch (error) {
      console.error('Failed to load channels:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectChannel = (channel) => {
    onSelectChannel(channel);
    onClose();
  };

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen || channels.length === 0) return;

    const handleKeyDown = (event) => {
      switch (event.key) {
        case 'ArrowUp':
          event.preventDefault();
          setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : channels.length - 1));
          break;
        case 'ArrowDown':
          event.preventDefault();
          setHighlightedIndex((prev) => (prev < channels.length - 1 ? prev + 1 : 0));
          break;
        case 'Enter':
          event.preventDefault();
          if (channels[highlightedIndex]) {
            handleSelectChannel(channels[highlightedIndex]);
          }
          break;
        case 'ArrowLeft':
          event.preventDefault();
          onClose();
          break;
        case 'Escape':
          event.preventDefault();
          onClose();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, channels, highlightedIndex]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="menu-backdrop" onClick={onClose} />

      {/* Menu sidebar */}
      <div className={`channel-menu ${isOpen ? 'open' : ''}`}>
        <div className="menu-header">
          <h2>Channels</h2>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="menu-content">
          {loading ? (
            <div className="loading">Loading channels...</div>
          ) : channels.length === 0 ? (
            <div className="empty-state">
              <p>No channels yet</p>
              <button onClick={onManage} className="primary">
                Create Channel
              </button>
            </div>
          ) : (
            <div className="channel-list">
              {channels.map((channel, index) => (
                <button
                  key={channel.id}
                  ref={(el) => (channelRefs.current[index] = el)}
                  className={`channel-item ${
                    channel.id === currentChannelId ? 'active' : ''
                  } ${index === highlightedIndex ? 'highlighted' : ''}`}
                  onClick={() => handleSelectChannel(channel)}
                  onMouseEnter={() => setHighlightedIndex(index)}
                >
                  <span className="channel-name">{channel.name}</span>
                  {channel.id === currentChannelId && (
                    <span className="playing-indicator">▶</span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="menu-footer">
          <button onClick={onManage} className="manage-btn">
            Manage Channels & Sources
          </button>
        </div>
      </div>
    </>
  );
}
