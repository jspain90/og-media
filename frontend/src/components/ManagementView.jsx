import { useState, useEffect } from 'react';
import {
  getChannels,
  createChannel,
  deleteChannel,
  getSources,
  createSource,
  deleteSource,
  rebuildQueue,
} from '../services/api';
import './ManagementView.css';

export function ManagementView({ onClose }) {
  const [channels, setChannels] = useState([]);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

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
      setChannels(data);
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
