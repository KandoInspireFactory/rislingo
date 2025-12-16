type SimpleLoginResponse = {
  session_token: string;
  user_id: string;
};

// Current (namespaced) keys
const SESSION_TOKEN_KEY = 'rislingo_session_token';
const USER_ID_KEY = 'rislingo_user_id';
const USER_IDENTIFIER_KEY = 'rislingo_user_identifier';

// Legacy keys used in some pages/components
const LEGACY_SESSION_TOKEN_KEY = 'session_token';
const LEGACY_USER_ID_KEY = 'user_id';
const LEGACY_USER_IDENTIFIER_KEY = 'user_identifier';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function simpleLogin(userIdentifier: string): Promise<SimpleLoginResponse> {
  const res = await fetch(`${API_BASE}/api/auth/simple-login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userIdentifier }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`ログインに失敗しました (${res.status}) ${text}`);
  }

  return res.json();
}

export function storeSessionToken(token: string) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(SESSION_TOKEN_KEY, token);
    // Keep legacy key for compatibility
    localStorage.setItem(LEGACY_SESSION_TOKEN_KEY, token);
  } catch (e) {
    // ignore quota errors
  }
}

export function storeUserId(id: string) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(USER_ID_KEY, id);
    // Keep legacy key for compatibility
    localStorage.setItem(LEGACY_USER_ID_KEY, id);
  } catch (e) {}
}

export function storeUserIdentifier(identifier: string) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(USER_IDENTIFIER_KEY, identifier);
    // Keep legacy key for compatibility
    localStorage.setItem(LEGACY_USER_IDENTIFIER_KEY, identifier);
  } catch (e) {}
}

export function getUserIdentifier(): string | null {
  if (typeof window === 'undefined') return null;
  // Prefer namespaced key, fallback to legacy key for older pages
  return localStorage.getItem(USER_IDENTIFIER_KEY) || localStorage.getItem(LEGACY_USER_IDENTIFIER_KEY);
}

export function clearSessionToken() {
  if (typeof window === 'undefined') return;
  try {
    // Remove both namespaced and legacy keys
    localStorage.removeItem(SESSION_TOKEN_KEY);
    localStorage.removeItem(USER_ID_KEY);
    localStorage.removeItem(USER_IDENTIFIER_KEY);
    localStorage.removeItem(LEGACY_SESSION_TOKEN_KEY);
    localStorage.removeItem(LEGACY_USER_ID_KEY);
    localStorage.removeItem(LEGACY_USER_IDENTIFIER_KEY);
  } catch (e) {}
}

export async function isAuthenticated(): Promise<boolean> {
  if (typeof window === 'undefined') return false;
  // Check both namespaced and legacy session token keys
  const token = localStorage.getItem(SESSION_TOKEN_KEY) || localStorage.getItem(LEGACY_SESSION_TOKEN_KEY);
  if (!token) return false;

  try {
    const res = await fetch(`${API_BASE}/api/auth/verify?session_token=${encodeURIComponent(token)}`);
    return res.ok;
  } catch (e) {
    console.error('isAuthenticated error', e);
    return false;
  }
}

export { SESSION_TOKEN_KEY, USER_ID_KEY, USER_IDENTIFIER_KEY };
