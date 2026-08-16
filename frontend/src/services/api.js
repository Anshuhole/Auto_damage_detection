const API_BASE = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace(/\/$/, '') : '';
const DEFAULT_BACKEND = API_BASE || 'http://127.0.0.1:8000';

/**
 * Smart fetch helper that prioritizes configured API_BASE or relative endpoint,
 * then automatically falls back to DEFAULT_BACKEND if needed.
 */
async function smartFetch(path, options = {}) {
  const targetUrl = API_BASE ? `${API_BASE}${path.startsWith('/') ? '' : '/'}${path}` : path;
  try {
    const res = await fetch(targetUrl, options);
    return res;
  } catch (err) {
    if (!targetUrl.startsWith('http')) {
      const fallbackUrl = `${DEFAULT_BACKEND}${path.startsWith('/') ? '' : '/'}${path}`;
      try {
        const fallbackRes = await fetch(fallbackUrl, options);
        return fallbackRes;
      } catch (fallbackErr) {
        throw new Error(`Unable to connect to AI Backend. Ensure the backend is running on ${DEFAULT_BACKEND}.`);
      }
    }
    throw err;
  }
}

/**
 * Predict damage from uploaded file.
 */
export async function predictImage(file, notes = '') {
  const formData = new FormData();
  formData.append('file', file);
  if (notes) {
    formData.append('notes', notes);
  }

  const response = await smartFetch('/api/predict', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Inference failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * Predict damage from webcam Base64 string.
 */
export async function predictBase64(imageBase64, filename = 'webcam_capture.jpg', notes = '') {
  const response = await smartFetch('/api/predict/base64', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image_base64: imageBase64,
      filename,
      notes,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Inference failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * Fetch inspection history.
 */
export async function getHistory(params = {}) {
  const query = new URLSearchParams();
  if (params.limit) query.append('limit', params.limit);
  if (params.offset) query.append('offset', params.offset);
  if (params.damage_type && params.damage_type !== 'all') query.append('damage_type', params.damage_type);
  if (params.severity && params.severity !== 'all') query.append('severity', params.severity);
  if (params.search) query.append('search', params.search);

  const response = await smartFetch(`/api/history?${query.toString()}`);
  if (!response.ok) throw new Error('Failed to fetch history');
  return response.json();
}

/**
 * Fetch single inspection details.
 */
export async function getInspectionDetail(id) {
  const response = await smartFetch(`/api/history/${id}`);
  if (!response.ok) throw new Error('Failed to fetch inspection details');
  return response.json();
}

/**
 * Delete inspection record.
 */
export async function deleteInspection(id) {
  const response = await smartFetch(`/api/history/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete inspection');
  return response.json();
}

/**
 * Fetch dashboard analytics stats.
 */
export async function getStats() {
  const response = await smartFetch('/api/stats');
  if (!response.ok) throw new Error('Failed to fetch stats');
  return response.json();
}

/**
 * Get PDF download URL.
 */
export function getReportPdfUrl(id) {
  return `/api/report/${id}/pdf`;
}

/**
 * Check backend health.
 */
export async function checkHealth() {
  try {
    const response = await smartFetch('/api/health');
    return response.ok;
  } catch {
    return false;
  }
}
