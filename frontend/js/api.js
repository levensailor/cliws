const API_BASE = '';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return null;
  }
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

export const api = {
  getTree: () => request('/api/tree'),
  createSection: (payload) => request('/api/sections', { method: 'POST', body: JSON.stringify(payload) }),
  updateSection: (id, payload) => request(`/api/sections/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteSection: (id) => request(`/api/sections/${id}`, { method: 'DELETE' }),
  createSubsection: (payload) => request('/api/subsections', { method: 'POST', body: JSON.stringify(payload) }),
  updateSubsection: (id, payload) => request(`/api/subsections/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteSubsection: (id) => request(`/api/subsections/${id}`, { method: 'DELETE' }),
  createEntry: (payload) => request('/api/entries', { method: 'POST', body: JSON.stringify(payload) }),
  updateEntry: (id, payload) => request(`/api/entries/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteEntry: (id) => request(`/api/entries/${id}`, { method: 'DELETE' }),
  reorder: (payload) => request('/api/reorder', { method: 'POST', body: JSON.stringify(payload) }),
  getIcons: () => request('/api/icons'),
  getSettings: () => request('/api/settings'),
};
