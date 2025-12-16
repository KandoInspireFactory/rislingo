const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

    // Parse response safely — server may return non-JSON or empty bodies
    let data: any = {};
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (parseErr) {
        data = { detail: text };
      }
    } else {
      data = { detail: res.statusText || 'No response body' };
    }

    // Log request details for debugging (only in development)
    if (process.env.NODE_ENV === 'development' && !res.ok) {
      try {
        console.error('API Request failed:');
        console.error('URL:', String(input));
        console.error('Method:', init?.method || 'GET');
        console.error('Status:', res?.status || 'no status');
        console.error('Status Text:', res?.statusText || 'no status text');
        console.error('Response Data:', data);
        console.error('Raw Text:', text);
        console.error('Content Type:', res?.headers?.get('content-type') || 'unknown');
        console.error('Has Response:', !!res);
        console.error('Has Text:', !!text);
        console.error('Has Data:', !!data);
        if (data && typeof data === 'object') {
          console.error('Data Keys:', Object.keys(data));
        }
      } catch (logError) {
        console.error('Error logging API failure:', logError);
        console.error('Basic error - URL:', String(input));
        console.error('Basic error - Status:', res?.status);
      }
    }

    if (!res.ok) {
      const status = res.status;
      
      // Extract error information from the response
      let userMessage = 'APIエラーが発生しました。';
      let errorDetails = data;
      
      // Handle structured error response from backend
      if (data?.error) {
        userMessage = data.error.user_message || userMessage;
        errorDetails = data.error.details || data.error.message || data.error;
      } else if (data?.detail) {
        errorDetails = data.detail;
      } else if (data?.message) {
        errorDetails = data.message;
      } else if (text) {
        errorDetails = text;
      }
      
      // Throw specific error types based on status code
      if (status === 401) throw new AuthenticationError(data?.error?.user_message);
      if (status === 429) throw new RateLimitError(data?.error?.user_message);
      if (status >= 500) throw new ServerError(data?.error?.user_message);
      
      throw new APIError(userMessage, errorDetails);
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
  // Ensure the blob has the correct type and filename extension
  const filename = audioBlob.type.includes('webm') ? 'recording.webm' : 
                   audioBlob.type.includes('mp4') ? 'recording.mp4' :
                   audioBlob.type.includes('wav') ? 'recording.wav' : 'recording.webm';
  fd.append('audio_file', audioBlob, filename);
  fd.append('problem_id', problemId);
  
  // Log audio blob details for debugging
  if (process.env.NODE_ENV === 'development') {
    console.log('🎤 Transcribing audio:', {
      size: audioBlob.size,
      type: audioBlob.type,
      filename: filename,
      problemId: problemId,
      url: url
    });
  }

  // Check if audio blob is valid
  if (audioBlob.size === 0) {
    throw new APIError('音声ファイルが空です。録音が正常に行われませんでした。');
  }

  // Check if audio blob is too small (likely invalid)
  if (audioBlob.size < 1000) { // Less than 1KB is probably invalid
    console.warn('⚠️ Audio blob is very small:', audioBlob.size, 'bytes');
    throw new APIError(`音声ファイルが小さすぎます（${audioBlob.size}バイト）。録音が正常に行われなかった可能性があります。`);
  }

  // Validate MIME type
  if (!audioBlob.type) {
    console.warn('⚠️ Audio blob has no MIME type');
    throw new APIError('音声ファイルの形式を判定できません。');
  }

  try {
    console.log('🚀 Sending transcription request to:', url);
    console.log('📤 Request details:', {
      audioSize: audioBlob.size,
      audioType: audioBlob.type,
      filename: filename,
      problemId: problemId
    });
    
    // Test backend connectivity first
    try {
      const healthCheck = await fetch(`${API_BASE}/health`, { method: 'GET' });
      console.log('🏥 Backend health check:', healthCheck.status);
    } catch (healthError) {
      console.error('❌ Backend health check failed:', healthError);
      throw new NetworkError('バックエンドサーバーに接続できません。サーバーが起動しているか確認してください。');
    }
    
    const res = await fetch(url, { method: 'POST', body: fd });
    console.log('📡 Transcription response received:', res?.status, res?.statusText);
    
    if (!res || !res.ok) {
      let rawText = '';
      let errorData: any = {};
      
      try {
        rawText = await res.text();
      } catch (textError) {
        console.warn('Failed to read response text:', textError);
        rawText = '';
      }
      
      try {
        errorData = rawText ? JSON.parse(rawText) : {};
      } catch (parseErr) {
        errorData = { detail: rawText || 'Unknown error' };
      }

      // Extract user-friendly error message
      let userMessage = '音声の文字起こしに失敗しました。';
      if (errorData?.error?.user_message) {
        userMessage = errorData.error.user_message;
      } else if (errorData?.detail) {
        userMessage = errorData.detail;
      } else if (rawText) {
        userMessage = rawText;
      }

      // Log detailed error for debugging (include rawText and headers)
      if (process.env.NODE_ENV === 'development') {
        try {
          const headersObj: Record<string, string> = {};
          if (res && res.headers && typeof res.headers.forEach === 'function') {
            res.headers.forEach((value, key) => {
              headersObj[key] = value;
            });
          }
          
          console.error('Transcription error (detailed):', {
            hasResponse: !!res,
            status: res?.status || 'no response',
            statusText: res?.statusText || 'no response',
            responseParsed: errorData,
            rawText: rawText || 'no raw text',
            url: url,
            contentType: res?.headers?.get('content-type') || 'unknown',
            headers: headersObj,
            audioSize: audioBlob.size,
            audioType: audioBlob.type,
            filename: filename
          });
        } catch (logError) {
          console.error('Transcription error (basic):', {
            hasResponse: !!res,
            status: res?.status || 'no response',
            statusText: res?.statusText || 'no response',
            url: url,
            errorMessage: userMessage,
            logError: String(logError),
            audioSize: audioBlob.size,
            audioType: audioBlob.type
          });
        }
      }

      throw new APIError(userMessage, errorData);
    }
    
    return res.json();
  } catch (err) {
    if (err instanceof APIError) throw err;
    
    // Log the actual error for debugging
    if (process.env.NODE_ENV === 'development') {
      console.error('Transcription network error:', {
        error: err,
        message: (err as Error)?.message,
        stack: (err as Error)?.stack,
        url: url,
        audioSize: audioBlob.size,
        audioType: audioBlob.type,
        errorType: typeof err,
        errorName: (err as Error)?.name
      });
    }
    
    // Check if it's a network connectivity issue
    const errorMessage = (err as Error)?.message || '';
    if (errorMessage.includes('fetch') || errorMessage.includes('network') || errorMessage.includes('Failed to fetch')) {
      throw new NetworkError('ネットワーク接続エラーです。バックエンドサーバーが起動しているか確認してください。');
    }
    
    throw new NetworkError(`音声処理中にエラーが発生しました: ${errorMessage}`);
  }
}

// Scoring
export async function evaluateResponse(payload: { problem_id: string; transcript: string; reading_text: string; lecture_script: string }) {
  const url = `${API_BASE}/api/scoring/evaluate`;
  return requestJSON<any>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
}

export async function evaluateTask1Response(payload: { problem_id: string; transcript: string; question: string }) {
  const url = `${API_BASE}/api/scoring/evaluate-task1`;
  return requestJSON<any>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
}

export async function generateModelAnswer(payload: { problem_id: string; reading_text: string; lecture_script: string; question: string }) {
  const url = `${API_BASE}/api/scoring/model-answer/generate`;
  return requestJSON<any>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
}

export async function generateTask1ModelAnswer(payload: { problem_id: string; question: string }) {
  const url = `${API_BASE}/api/scoring/model-answer/generate-task1`;
  return requestJSON<any>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
}

export async function generateTask2ModelAnswer(payload: { problem_id: string; announcement_text: string; conversation_script: string; question: string }) {
  const url = `${API_BASE}/api/scoring/model-answer/generate-task2`;
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

// Task1 Archive
export async function getTask1Questions(userIdentifier: string, limit = 50, offset = 0) {
  const url = `${API_BASE}/api/task1-archive/questions?user_id=${encodeURIComponent(userIdentifier)}&limit=${limit}&offset=${offset}`;
  return requestJSON<any>(url, { method: 'GET' });
}

export async function getTask1Question(questionId: string, userIdentifier: string) {
  const url = `${API_BASE}/api/task1-archive/questions/${encodeURIComponent(questionId)}?user_id=${encodeURIComponent(userIdentifier)}`;
  return requestJSON<any>(url, { method: 'GET' });
}

// Misc
export async function fetchHistoryForUser(userIdentifier: string, limit = 3) {
  return fetchHistory(userIdentifier, limit);
}

// AI Review
export async function generateAIReview(payload: { 
  task_type: string; 
  problem_id: string; 
  user_transcript: string; 
  question: string;
  reading_text?: string;
  lecture_script?: string;
  announcement_text?: string;
  conversation_script?: string;
}) {
  const url = `${API_BASE}/api/scoring/ai-review`;
  
  // Log request details for debugging
  if (process.env.NODE_ENV === 'development') {
    console.log('🔍 AI Review Request:', {
      url: url,
      payload: payload,
      payloadSize: JSON.stringify(payload).length
    });
  }
  
  return requestJSON<any>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
}

// Generate speech audio from text
export async function generateSpeechAudio(text: string): Promise<Blob> {
  const url = `${API_BASE}/api/scoring/generate-speech`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });
    
    if (!response.ok) {
      throw new APIError(`音声生成に失敗しました: ${response.status}`);
    }
    
    return await response.blob();
  } catch (error) {
    console.error('Speech generation error:', error);
    throw new APIError('音声生成中にエラーが発生しました。');
  }
}

export type RecordingErrorType = RecordingError;

export { fetchHistory as fetchHistoryAPI, transcribeAudio as transcribeAudioAPI };
