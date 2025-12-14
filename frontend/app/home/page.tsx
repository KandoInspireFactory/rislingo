'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, clearSessionToken, getUserIdentifier } from '@/lib/auth';
import { fetchHistory } from '@/lib/api-client';
import { PracticeSessionSummary } from '@/lib/types';
import RecentSessions from '@/components/RecentSessions';
import LoadingSpinner from '@/components/LoadingSpinner';

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(true);
  const [sessions, setSessions] = useState<PracticeSessionSummary[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const router = useRouter();

  const loadHistory = useCallback(async () => {
    setIsLoadingSessions(true);
    try {
      const userIdentifier = getUserIdentifier();
      if (userIdentifier) {
        const history = await fetchHistory(userIdentifier, 3);
        setSessions(history.sessions);
      }
    } catch (error) {
      console.error('Failed to load history:', error);
      // Don't show error to user, just show empty state
      setSessions([]);
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  useEffect(() => {
    const checkAuth = async () => {
      const authenticated = await isAuthenticated();
      if (!authenticated) {
        router.push('/login');
      } else {
        setIsLoading(false);
        loadHistory();
      }
    };

    checkAuth();
  }, [router, loadHistory]);

  const handleLogout = () => {
    clearSessionToken();
    router.push('/login');
  };

  const handleStartPractice = () => {
    // Navigate to Task Selection Page
    router.push('/practice/select');
  };

  const handleFlashcards = () => {
    router.push('/flashcards/select');
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--background)' }}>
      {/* Header */}
      <header className="surface-elevated backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
          <h1 className="text-xl sm:text-2xl font-bold text-luxury">
            TOEFL Speaking Master
          </h1>
          <button
            onClick={handleLogout}
            className="text-sm hover:text-luxury transition-all duration-300"
            style={{ color: 'var(--foreground-muted)' }}
          >
            ログアウト
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
        {/* Welcome Section */}
        <div className="text-center mb-12 sm:mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4 sm:mb-6" style={{ color: 'var(--foreground)' }}>
            ようこそ！
          </h2>
          <p className="text-lg sm:text-xl gold-accent font-light tracking-wide">
            TOEFL Speaking Task 3の練習を始めましょう
          </p>
        </div>

        {/* Action Cards */}
        <div className="grid sm:grid-cols-2 gap-6 sm:gap-8 max-w-5xl mx-auto mb-12 sm:mb-16">
          <button 
            onClick={handleStartPractice}
            className="luxury-card rounded-2xl p-8 sm:p-10 text-left group relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-yellow-500/10 to-transparent rounded-full blur-2xl"></div>
            <div className="relative">
              <div className="w-14 h-14 rounded-xl flex items-center justify-center mb-6 gold-gradient">
                <svg className="w-7 h-7" style={{ color: 'var(--color-black-50)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold mb-3 gold-accent">
                練習を始める
              </h3>
              <p className="text-sm sm:text-base font-light tracking-wide" style={{ color: 'var(--foreground-muted)' }}>
                TOEFL Speaking練習を始めましょう
              </p>
            </div>
          </button>

          <button 
            onClick={handleFlashcards}
            className="luxury-card rounded-2xl p-8 sm:p-10 text-left group relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-yellow-500/10 to-transparent rounded-full blur-2xl"></div>
            <div className="relative">
              <div className="w-14 h-14 rounded-xl flex items-center justify-center mb-6" style={{ 
                background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%)',
                border: '1px solid var(--border-color-gold)'
              }}>
                <svg className="w-7 h-7 gold-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold mb-3" style={{ color: 'var(--foreground)' }}>
                フラッシュカード
              </h3>
              <p className="text-sm sm:text-base font-light tracking-wide" style={{ color: 'var(--foreground-muted)' }}>
                フラッシュカードで復習
              </p>
            </div>
          </button>
        </div>

        {/* Recent Sessions */}
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-px flex-1" style={{ background: 'var(--border-color)' }}></div>
            <h3 className="text-lg sm:text-xl font-semibold tracking-wide" style={{ color: 'var(--foreground)' }}>
              最近の学習履歴
            </h3>
            <div className="h-px flex-1" style={{ background: 'var(--border-color)' }}></div>
          </div>
          <RecentSessions sessions={sessions} isLoading={isLoadingSessions} />
        </div>
      </main>
    </div>
  );
}
