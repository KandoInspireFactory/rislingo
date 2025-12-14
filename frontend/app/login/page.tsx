'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { simpleLogin, storeSessionToken, storeUserId, storeUserIdentifier } from '@/lib/auth';

export default function LoginPage() {
  const [userId, setUserId] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (!userId.trim()) {
        setError('ユーザーIDを入力してください');
        setIsLoading(false);
        return;
      }

      const response = await simpleLogin(userId.trim());
      storeSessionToken(response.session_token);
      storeUserId(response.user_id); // Store UUID from backend
      storeUserIdentifier(userId.trim()); // Store the login identifier
      
      console.log('✅ Login successful');
      console.log('Session token:', response.session_token);
      console.log('User ID (UUID):', response.user_id);
      console.log('User identifier:', userId.trim());
      
      // Redirect to home page after successful login
      router.push('/home');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ログインに失敗しました');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden" style={{ background: 'var(--background)' }}>
      {/* Luxury background effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-yellow-500/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-yellow-500/5 rounded-full blur-3xl"></div>
      </div>

      <div className="w-full max-w-md relative z-10">
        <div className="luxury-card rounded-3xl p-10 backdrop-blur-sm">
          <div className="text-center mb-10">
            <h1 className="text-4xl font-bold mb-3 text-luxury">
              TOEFL Speaking Master
            </h1>

          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label 
                htmlFor="userId" 
                className="block text-sm font-medium mb-3 tracking-wide"
                style={{ color: 'var(--foreground)' }}
              >
                ユーザーID
              </label>
              <input
                id="userId"
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="例: user123"
                className="w-full px-5 py-4 rounded-xl outline-none transition-all font-light"
                style={{
                  background: 'var(--background-elevated)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--foreground)'
                }}
                onFocus={(e) => e.target.style.borderColor = 'var(--color-accent-gold)'}
                onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
                disabled={isLoading}
              />
            </div>

            {error && (
              <div className="px-5 py-4 rounded-xl text-sm font-light" style={{
                background: 'rgba(220, 38, 38, 0.1)',
                border: '1px solid rgba(220, 38, 38, 0.3)',
                color: '#fca5a5'
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="btn-luxury w-full py-4 px-6 rounded-xl font-semibold tracking-wide disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'ログイン中...' : 'ログイン'}
            </button>
          </form>

          <div className="mt-8 text-center text-sm font-light tracking-wide" style={{ color: 'var(--foreground-muted)' }}>
            <p>初めての方は、任意のユーザーIDを入力してください</p>
          </div>
        </div>
      </div>
    </div>
  );
}
