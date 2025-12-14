import os

content = r"""const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Error classes
export class APIError extends Error {
  userMessage: string;
  details?: unknown;
  constructor(userMessage: string, details?: unknown) {
    super(userMessage);
    this.name = 'APIError';
    this.userMessage = userMessage;
    this.details = details;
  }
}

export class NetworkError extends Error {
  constructor(message = 'Network error') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class RateLimitError extends APIError {
  constructor(userMessage = 'リクエスト回数の上限に達しました。しばらく待ってから再試行してください。') {
    super(userMessage);
    this.name = 'RateLimitError';
  }
}

export class ServerError extends APIError {
  constructor(userMessage = 'サーバーエラーが発生しました。') {
    super(userMessage);
    this.name = 'ServerError';
  }
}

export class AuthenticationError extends APIError {
  constructor(userMessage = '認証エラーが発生しました。ログインし直してください。') {
    super(userMessage);
    this.name = 'AuthenticationError';
  }
}

export class ValidationError extends APIError {
  details?: Record<string, unknown>;
  constructor(userMessage = '入力エラーがあります。', details?: Record<string, unknown>) {
    super(userMessage, details);
    this.name = 'ValidationError';
    this.details = details;
  }
}

export class RecordingError extends Error {
  constructor(message = '録音エラー') {
    super(message);
    this.name = 'RecordingError';
  }
}

// Helper for JSON requests
async function requestJSON<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  try {
    const res = await fetch(input, init);
    const text = await res.text();
    const data = text ? JSON.parse(text) : {};

    if (!res.ok) {
      const status = res.status;
      const detail = data?.detail || data?.error || data || text;
      if (status === 401) throw new AuthenticationError();
      if (status === 429) throw new RateLimitError();
      if (status >= 500) throw new ServerError();
      throw new APIError('APIエラーが発生しました。', detail);
    }

    return data as T;
  } catch (err) {
    if (err instanceof APIError || err instanceof AuthenticationError || err instanceof ServerError || err instanceof RateLimitError) throw err;
    throw new NetworkError((err as Error)?.message || 'Network error');
  }
}

// History
export async function fetchHistory(userIdentifier: string, limit = 3) {
  const url = `${API_BASE}/api/history?user_id=${encodeURIComponent(userIdentifier)}&limit=${encodeURIComponent(String(limit))}`;
  return requestJSON<{ sessions: any[]; total: number }>(url, { method: 'GET' });
}

export async function fetchSessionDetail(sessionId: string, userIdentifier: string) {
  const url = `${API_BASE}/api/history/${encodeURIComponent(sessionId)}?user_id=${encodeURIComponent(userIdentifier)}`;
  return requestJSON<any>(url, { method: 'GET' });
}

// Problems
export async function generateProblem(userIdentifier: string, task_type = 'task3', topic_category?: string) {
  const url = `${API_BASE}/api/problems/generate`;
  const body = { task_type, topic_category, user_id: userIdentifier };
  return requestJSON<any>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
}

// Speech (upload audio blob)
export async function transcribeAudio(audioBlob: Blob, problemId: string) {
  const url = `${API_BASE}/api/speech/transcribe`;
  const fd = new FormData();
  fd.append('audio_file', audioBlob, 'recording.webm');
  fd.append('problem_id', problemId);

  try {
    const res = await fetch(url, { method: 'POST', body: fd });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new APIError(`Transcription failed: ${res.status}`, text);
    }
    return res.json();
  } catch (err) {
    if (err instanceof APIError) throw err;
    throw new NetworkError((err as Error)?.message || 'Transcription network error');
  }
}

// Scoring
export async function evaluateResponse(payload: { problem_id: string; transcript: string; reading_text: string; lecture_script: string }) {
  const url = `${API_BASE}/api/scoring/evaluate`;
  return requestJSON<any>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
}

export async function generateModelAnswer(payload: { problem_id: string; reading_text: string; lecture_script: string; question: string }) {
  const url = `${API_BASE}/api/scoring/model-answer/generate`;
  return requestJSON<any>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
}

// Phrases
export async function savePhrase(userIdentifier: string, phrase: string, context = '', category = '') {
  const url = `${API_BASE}/api/phrases`;
  const body = { user_id: userIdentifier, phrase, context, category };
  return requestJSON<any>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
}

export async function getPhrases(userIdentifier: string) {
  const url = `${API_BASE}/api/phrases?user_id=${encodeURIComponent(userIdentifier)}`;
  return requestJSON<any>(url, { method: 'GET' });
}

export async function deletePhrase(phraseId: string, userIdentifier: string) {
  const url = `${API_BASE}/api/phrases/${encodeURIComponent(phraseId)}?user_id=${encodeURIComponent(userIdentifier)}`;
  return requestJSON<any>(url, { method: 'DELETE' });
}

export async function updatePhraseMastered(phraseId: string, userIdentifier: string, is_mastered: boolean) {
  const url = `${API_BASE}/api/phrases/${encodeURIComponent(phraseId)}?user_id=${encodeURIComponent(userIdentifier)}`;
  return requestJSON<any>(url, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ is_mastered }) });
}

// Misc
export async function fetchHistoryForUser(userIdentifier: string, limit = 3) {
  return fetchHistory(userIdentifier, limit);
}

export type RecordingErrorType = RecordingError;

export { fetchHistory as fetchHistoryAPI, transcribeAudio as transcribeAudioAPI };
"""

with open('frontend/lib/api-client.ts', 'w') as f:
    f.write(content)
