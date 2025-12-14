'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, getUserIdentifier } from '@/lib/auth';
import { getPhrases, updatePhraseMastered } from '@/lib/api-client';
import type { SavedPhrase } from '@/lib/types';
import FlashCard from '@/components/FlashCard';
import LoadingSpinner from '@/components/LoadingSpinner';

/**
 * Flashcards review page for reviewing saved phrases.
 * Displays phrases in random order and tracks mastery progress.
 */
export default function FlashcardsReviewPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [phrases, setPhrases] = useState<SavedPhrase[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const router = useRouter();

  // Shuffle array using Fisher-Yates algorithm
  const shuffleArray = <T,>(array: T[]): T[] => {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  };

  const loadPhrases = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const userIdentifier = getUserIdentifier();
      if (!userIdentifier) {
        router.push('/login');
        return;
      }

      const response = await getPhrases(userIdentifier);
      const phrases = response.phrases as SavedPhrase[];
      
      if (phrases.length === 0) {
        setError('保存されたフレーズがありません。まず練習を始めて、フレーズを保存してください。');
        setPhrases([]);
      } else {
        // Shuffle phrases for random display order
        const shuffledPhrases = shuffleArray(phrases);
        setPhrases(shuffledPhrases);
        setCurrentIndex(0);
      }
    } catch (err) {
      console.error('Failed to load phrases:', err);
      setError('フレーズの読み込みに失敗しました。もう一度お試しください。');
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  useEffect(() => {
    const checkAuth = async () => {
      const authenticated = await isAuthenticated();
      if (!authenticated) {
        router.push('/login');
      } else {
        loadPhrases();
      }
    };

    checkAuth();
  }, [router, loadPhrases]);

  const handleMastered = async () => {
    if (isUpdating || phrases.length === 0) return;

    setIsUpdating(true);
    try {
      const userIdentifier = getUserIdentifier();
      if (!userIdentifier) return;

      const currentPhrase = phrases[currentIndex];
      await updatePhraseMastered(currentPhrase.id, userIdentifier, true);

      // Move to next card
      moveToNextCard();
    } catch (err) {
      console.error('Failed to update phrase:', err);
      // Still move to next card even if update fails
      moveToNextCard();
    } finally {
      setIsUpdating(false);
    }
  };

  const handleNotYet = async () => {
    if (isUpdating || phrases.length === 0) return;

    setIsUpdating(true);
    try {
      const userIdentifier = getUserIdentifier();
      if (!userIdentifier) return;

      const currentPhrase = phrases[currentIndex];
      await updatePhraseMastered(currentPhrase.id, userIdentifier, false);

      // Move to next card
      moveToNextCard();
    } catch (err) {
      console.error('Failed to update phrase:', err);
      // Still move to next card even if update fails
      moveToNextCard();
    } finally {
      setIsUpdating(false);
    }
  };

  const moveToNextCard = () => {
    if (currentIndex < phrases.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      // Reached the end, show completion message
      setError('全てのフレーズを確認しました！');
    }
  };

  const handleBackToSelect = () => {
    router.push('/flashcards/select');
  };

  const handleRestart = () => {
    loadPhrases();
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error && phrases.length === 0) {
    return (
      <div className="min-h-screen" style={{ background: 'var(--background)' }}>
        <header className="surface-elevated backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
            <h1 className="text-xl sm:text-2xl font-bold text-luxury">
              フラッシュカード
            </h1>
            <button
              onClick={handleBackToSelect}
              className="text-sm hover:text-luxury transition-all duration-300"
              style={{ color: 'var(--foreground-muted)' }}
            >
              戻る
            </button>
          </div>
        </header>
        <div className="flex items-center justify-center min-h-[calc(100vh-80px)]">
          <div className="max-w-md mx-auto px-4 text-center">
            <div className="surface-card rounded-2xl p-8">
              <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4" style={{
                background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%)',
                border: '1px solid var(--border-color-gold)'
              }}>
                <svg className="w-8 h-8 gold-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--foreground)' }}>フレーズがありません</h2>
              <p className="mb-6" style={{ color: 'var(--foreground-muted)' }}>{error}</p>
              <div className="flex flex-col gap-3">
                <button
                  onClick={handleBackToSelect}
                  className="btn-primary"
                >
                  戻る
                </button>
                <button
                  onClick={loadPhrases}
                  className="btn-secondary"
                >
                  再読み込み
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const currentPhrase = phrases[currentIndex];
  const isComplete = currentIndex >= phrases.length;

  return (
    <div className="min-h-screen" style={{ background: 'var(--background)' }}>
      {/* Header */}
      <header className="surface-elevated backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
          <h1 className="text-xl sm:text-2xl font-bold text-luxury">
            フラッシュカード
          </h1>
          <button
            onClick={handleBackToSelect}
            className="text-sm hover:text-luxury transition-all duration-300"
            style={{ color: 'var(--foreground-muted)' }}
          >
            戻る
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Progress Display */}
        <div className="text-center mb-8">
          <p className="text-lg sm:text-xl font-semibold gold-accent">
            進捗: {Math.min(currentIndex + 1, phrases.length)} / {phrases.length}
          </p>
        </div>

        {/* Flashcard or Completion Message */}
        {isComplete ? (
          <div className="max-w-2xl mx-auto text-center">
            <div className="surface-card rounded-2xl p-8 sm:p-12">
              <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6" style={{
                background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(34, 197, 94, 0.1) 100%)',
                border: '1px solid rgba(34, 197, 94, 0.3)'
              }}>
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold mb-4" style={{ color: 'var(--foreground)' }}>
                完了しました！
              </h2>
              <p className="text-base sm:text-lg mb-8" style={{ color: 'var(--foreground-muted)' }}>
                全てのフレーズを確認しました。素晴らしい！
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={handleRestart}
                  className="btn-primary"
                >
                  もう一度復習する
                </button>
                <button
                  onClick={handleBackToSelect}
                  className="btn-secondary"
                >
                  戻る
                </button>
              </div>
            </div>
          </div>
        ) : (
          currentPhrase && (
            <FlashCard
              phrase={currentPhrase}
              onMastered={handleMastered}
              onNotYet={handleNotYet}
            />
          )
        )}

        {/* Loading Overlay */}
        {isUpdating && (
          <div className="fixed inset-0 bg-black bg-opacity-20 flex items-center justify-center z-50">
            <div className="surface-card rounded-lg p-4">
              <LoadingSpinner />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}