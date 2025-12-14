'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, getUserIdentifier } from '@/lib/auth';
import { getTask1Questions } from '@/lib/api-client';
import type { Task1Question } from '@/lib/types';
import Task1QuestionCard from '../../../components/Task1QuestionCard';
import LoadingSpinner from '@/components/LoadingSpinner';

/**
 * Task1 Archive page for reviewing past Task1 questions.
 * Displays questions in a flashcard-like interface.
 */
export default function Task1ArchivePage() {
  const [isLoading, setIsLoading] = useState(true);
  const [questions, setQuestions] = useState<Task1Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
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

  const loadQuestions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const userIdentifier = getUserIdentifier();
      if (!userIdentifier) {
        router.push('/login');
        return;
      }

      const response = await getTask1Questions(userIdentifier);
      const questionList = response.questions as Task1Question[];
      
      if (questionList.length === 0) {
        setError('保存されたTask1問題がありません。まずTask1の練習を始めて、問題を蓄積してください。');
        setQuestions([]);
      } else {
        // Shuffle questions for random display order
        const shuffledQuestions = shuffleArray(questionList);
        setQuestions(shuffledQuestions);
        setCurrentIndex(0);
      }
    } catch (err) {
      console.error('Failed to load Task1 questions:', err);
      setError('Task1問題の読み込みに失敗しました。もう一度お試しください。');
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
        loadQuestions();
      }
    };

    checkAuth();
  }, [router, loadQuestions]);

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      // Reached the end, show completion message
      setError('全てのTask1問題を確認しました！');
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleBackToSelect = () => {
    router.push('/flashcards/select');
  };

  const handleRestart = () => {
    loadQuestions();
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error && questions.length === 0) {
    return (
      <div className="min-h-screen" style={{ background: 'var(--background)' }}>
        <header className="surface-elevated backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
            <h1 className="text-xl sm:text-2xl font-bold text-luxury">
              Task1過去問題
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
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(59, 130, 246, 0.1) 100%)',
                border: '1px solid rgba(59, 130, 246, 0.3)'
              }}>
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--foreground)' }}>Task1問題がありません</h2>
              <p className="mb-6" style={{ color: 'var(--foreground-muted)' }}>{error}</p>
              <div className="flex flex-col gap-3">
                <button
                  onClick={handleBackToSelect}
                  className="btn-primary"
                >
                  戻る
                </button>
                <button
                  onClick={loadQuestions}
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

  const currentQuestion = questions[currentIndex];
  const isComplete = currentIndex >= questions.length;

  return (
    <div className="min-h-screen" style={{ background: 'var(--background)' }}>
      {/* Header */}
      <header className="surface-elevated backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
          <h1 className="text-xl sm:text-2xl font-bold text-luxury">
            Task1過去問題
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
          <p className="text-lg sm:text-xl font-semibold text-blue-600">
            進捗: {Math.min(currentIndex + 1, questions.length)} / {questions.length}
          </p>
        </div>

        {/* Question Card or Completion Message */}
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
                全てのTask1問題を確認しました。素晴らしい！
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
          currentQuestion && (
            <Task1QuestionCard
              question={currentQuestion}
              onNext={handleNext}
              onPrevious={handlePrevious}
              canGoNext={currentIndex < questions.length - 1}
              canGoPrevious={currentIndex > 0}
            />
          )
        )}
      </main>
    </div>
  );
}