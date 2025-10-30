const API_BASE =
  (import.meta.env.VITE_API_BASE ?? '/api').replace(/\/$/, '');

// Generic fetch wrapper
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

// ============ Channels ============

export async function getChannels() {
  return apiFetch('/channels/');
}

export async function getChannel(channelId) {
  return apiFetch(`/channels/${channelId}`);
}

export async function createChannel(name, playOrder = 'random') {
  return apiFetch('/channels/', {
    method: 'POST',
    body: JSON.stringify({ name, play_order: playOrder }),
  });
}

export async function updateChannel(channelId, updates) {
  return apiFetch(`/channels/${channelId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function deleteChannel(channelId) {
  return apiFetch(`/channels/${channelId}`, {
    method: 'DELETE',
  });
}

// ============ Sources ============

export async function getSources(channelId = null) {
  const query = channelId ? `?channel_id=${channelId}` : '';
  return apiFetch(`/sources/${query}`);
}

export async function getSource(sourceId) {
  return apiFetch(`/sources/${sourceId}`);
}

export async function createSource(channelId, youtubeId, sourceType, name = null) {
  return apiFetch('/sources/', {
    method: 'POST',
    body: JSON.stringify({
      channel_id: channelId,
      youtube_id: youtubeId,
      source_type: sourceType,
      name,
    }),
  });
}

export async function updateSource(sourceId, channelId, youtubeId, sourceType, name = null) {
  return apiFetch(`/sources/${sourceId}`, {
    method: 'PUT',
    body: JSON.stringify({
      channel_id: channelId,
      youtube_id: youtubeId,
      source_type: sourceType,
      name,
    }),
  });
}

export async function deleteSource(sourceId) {
  return apiFetch(`/sources/${sourceId}`, {
    method: 'DELETE',
  });
}

// ============ Player ============

export async function getNextVideo(channelId) {
  return apiFetch(`/player/play/${channelId}`);
}

export async function skipVideo(channelId, currentVideoId) {
  return apiFetch(`/player/skip/${channelId}`, {
    method: 'POST',
    body: JSON.stringify({ current_video_id: currentVideoId }),
  });
}

export async function getQueueStatus(channelId) {
  return apiFetch(`/player/status/${channelId}`);
}

export async function rebuildQueue(channelId) {
  return apiFetch(`/player/rebuild/${channelId}`, {
    method: 'POST',
  });
}

export async function rebuildAllQueues() {
  return apiFetch('/player/rebuild-all', {
    method: 'POST',
  });
}
