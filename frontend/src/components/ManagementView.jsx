import { useState, useEffect } from 'react';
import {
  getChannels,
  createChannel,
  deleteChannel,
  getSources,
  createSource,
  deleteSource,
  rebuildQueue,
  updateChannel,
} from '../services/api';
import './ManagementView.css';

const PLAY_ORDER_OPTIONS = [
  {
    value: 'random',
    label: 'Random (shuffle everything)',
    description: 'Mix videos from all sources randomly.',
  },
  {
    value: 'chronological_newest',
    label: 'Newest uploads (round robin)',
    description: "Rotate across sources and pick each source's newest video.",
  },
  {
    value: 'chronological_oldest',
    label: 'Oldest uploads (round robin)',
    description: "Rotate across sources and pick each source's oldest video.",
  },
];

export function ManagementView({ onClose }) {
  const [channels, setChannels] = useState([]);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);

  // Forms
  const [newChannelName, setNewChannelName] = useState('');
  const [showSourceForm, setShowSourceForm] = useState(false);
  const [newSource, setNewSource] = useState({
    youtube_id: '',
    source_type: 'channel',
    name: '',
  });

  useEffect(() => {
    loadChannels();
  }, []);

  useEffect(() => {
    if (selectedChannel) {
      loadSources(selectedChannel.id);
    }
  }, [selectedChannel]);

  const loadChannels = async () => {
    try {
      const data = await getChannels();
      const sorted = [...data].sort((a, b) => a.name.localeCompare(b.name));
      setChannels(sorted);
      if (selectedChannel) {
        const updated = sorted.find((channel) => channel.id === selectedChannel.id);
        if (updated) {
          setSelectedChannel(updated);
        }
      }
    } catch (error) {
      console.error('Failed to load channels:', error);
    }
  };

  const loadSources = async (channelId) => {
    try {
      const data = await getSources(channelId);
      setSources(data);
    } catch (error) {
      console.error('Failed to load sources:', error);
    }
  };

  const handleCreateChannel = async (e) => {
    e.preventDefault();
    if (!newChannelName.trim()) return;

    try {
      const channel = await createChannel(newChannelName);
      // Add new channel and sort alphabetically
      setChannels([...channels, channel].sort((a, b) => a.name.localeCompare(b.name)));
      setNewChannelName('');
      setSelectedChannel(channel);
    } catch (error) {
      alert('Failed to create channel: ' + error.message);
    }
  };

  const handleDeleteChannel = async (channelId) => {
    if (!confirm('Delete this channel and all its sources?')) return;

    try {
      await deleteChannel(channelId);
      setChannels(channels.filter((c) => c.id !== channelId));
      if (selectedChannel?.id === channelId) {
        setSelectedChannel(null);
      }
    } catch (error) {
      alert('Failed to delete channel: ' + error.message);
    }
  };

  const handleCreateSource = async (e) => {
    e.preventDefault();
    if (!newSource.youtube_id.trim() || !selectedChannel) return;

    try {
      await createSource(
        selectedChannel.id,
        newSource.youtube_id,
        newSource.source_type,
        newSource.name || null
      );
      loadSources(selectedChannel.id);
      setNewSource({ youtube_id: '', source_type: 'channel', name: '' });
      setShowSourceForm(false);
    } catch (error) {
      alert('Failed to add source: ' + error.message);
    }
  };

  const handleDeleteSource = async (sourceId) => {
    if (!confirm('Remove this source?')) return;

    try {
      await deleteSource(sourceId);
      setSources(sources.filter((s) => s.id !== sourceId));
    } catch (error) {
      alert('Failed to delete source: ' + error.message);
    }
  };

  const handleRebuildQueue = async () => {
    if (!selectedChannel) return;

    setLoading(true);
    try {
      const result = await rebuildQueue(selectedChannel.id);
      alert(result.message);
    } catch (error) {
      alert('Failed to rebuild queue: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayOrderChange = async (event) => {
    if (!selectedChannel) return;

    const newOrder = event.target.value;
    if (newOrder === selectedChannel.play_order) {
      return;
    }

    setSavingSettings(true);
    try {
      const updated = await updateChannel(selectedChannel.id, {
        play_order: newOrder,
      });

      const nextChannels = [...channels]
        .map((channel) => (channel.id === updated.id ? updated : channel))
        .sort((a, b) => a.name.localeCompare(b.name));

      setChannels(nextChannels);
      setSelectedChannel(updated);
    } catch (error) {
      alert('Failed to update channel: ' + error.message);
    } finally {
      setSavingSettings(false);
    }
  };

  return (
    <div className="management-view">
      <div className="management-header">
        <h1>Manage Channels & Sources</h1>
        <button onClick={onClose} className="close-btn">
          Back to Player
        </button>
      </div>

      <div className="management-content">
        {/* Left panel: Channels */}
        <div className="channels-panel">
          <div className="panel-header">
            <h2>Channels</h2>
          </div>

          <form onSubmit={handleCreateChannel} className="create-form">
            <input
              type="text"
              value={newChannelName}
              onChange={(e) => setNewChannelName(e.target.value)}
              placeholder="New channel name..."
            />
            <button type="submit" className="primary">
              Create
            </button>
          </form>

          <div className="channel-list">
            {channels.map((channel) => (
              <div
                key={channel.id}
                className={`channel-card ${
                  selectedChannel?.id === channel.id ? 'selected' : ''
                }`}
                onClick={() => setSelectedChannel(channel)}
              >
                <span className="channel-name">{channel.name}</span>
                <button
                  className="delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteChannel(channel.id);
                  }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel: Sources */}
        <div className="sources-panel">
          <div className="panel-header">
            <h2>
              {selectedChannel
                ? `Sources for "${selectedChannel.name}"`
                : 'Select a channel'}
            </h2>
            {selectedChannel && (
              <button
                onClick={handleRebuildQueue}
                disabled={loading}
                className="rebuild-btn"
              >
                {loading ? 'Rebuilding...' : 'Rebuild Queue'}
              </button>
            )}
          </div>

          {selectedChannel ? (
            <>
              {!showSourceForm ? (
                <button
                  onClick={() => setShowSourceForm(true)}
                  className="primary add-source-btn"
                >
                  Add Source
                </button>
              ) : (
                <form onSubmit={handleCreateSource} className="source-form">
                  <div className="form-row">
                    <select
                      value={newSource.source_type}
                      onChange={(e) =>
                        setNewSource({ ...newSource, source_type: e.target.value })
                      }
                    >
                      <option value="channel">YouTube Channel</option>
                      <option value="playlist">YouTube Playlist</option>
                    </select>
                  </div>

                  <div className="form-row">
                    <input
                      type="text"
                      value={newSource.youtube_id}
                      onChange={(e) =>
                        setNewSource({ ...newSource, youtube_id: e.target.value })
                      }
                      placeholder={
                        newSource.source_type === 'channel'
                          ? 'Paste @handle, URL, or channel ID'
                          : 'Playlist ID (e.g., PL...)'
                      }
                      required
                    />
                    {newSource.source_type === 'channel' && (
                      <small className="form-hint">
                        Examples: @RickBeato, https://youtube.com/@RickBeato, or UC...
                      </small>
                    )}
                  </div>

                  <div className="form-row">
                    <input
                      type="text"
                      value={newSource.name}
                      onChange={(e) =>
                        setNewSource({ ...newSource, name: e.target.value })
                      }
                      placeholder="Optional friendly name (auto-filled if empty)"
                    />
                  </div>

                  <div className="form-actions">
                    <button type="submit" className="primary">
                      Add
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowSourceForm(false);
                        setNewSource({ youtube_id: '', source_type: 'channel', name: '' });
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}

              <div className="channel-settings">
                <div className="form-row">
                  <label htmlFor="play-order-select">
                    Playback order
                  </label>
                  <select
                    id="play-order-select"
                    value={selectedChannel.play_order}
                    onChange={handlePlayOrderChange}
                    disabled={savingSettings}
                  >
                    {PLAY_ORDER_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-row">
                  <small className="form-hint">
                    {PLAY_ORDER_OPTIONS.find(
                      (option) => option.value === selectedChannel.play_order
                    )?.description || 'Choose how this channel queues videos.'}{' '}
                    The queue is automatically rebuilt after changing playback order.
                  </small>
                </div>
              </div>

              <div className="source-list">
                {sources.length === 0 ? (
                  <div className="empty-state">
                    <p>No sources yet. Add YouTube channels or playlists above.</p>
                  </div>
                ) : (
                  sources.map((source) => (
                    <div key={source.id} className="source-card">
                      <div className="source-info">
                        <div className="source-type-badge">{source.source_type}</div>
                        <div className="source-details">
                          <div className="source-name">
                            {source.name || source.youtube_id}
                          </div>
                          <div className="source-id">{source.youtube_id}</div>
                        </div>
                      </div>
                      <button
                        className="delete-btn"
                        onClick={() => handleDeleteSource(source.id)}
                      >
                        ✕
                      </button>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p>Select a channel to manage its sources</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}



