/**
 * Reading Phase - Task 3 Practice Flow
 * 
 * Features:
 * - Display reading material text
 * - 45-second countdown timer
 * - Progress bar showing phase progression
 * - Auto-transition to Listening Phase when timer completes
 * 
 * Requirements: 3.1
 */

'use client';

import { useEffect, useState, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Timer from '@/components/Timer';
import LoadingSpinner from '@/components/LoadingSpinner';
import { Problem } from '@/lib/types';
import { generateProblem } from '@/lib/api-client';
import { getUserIdentifier } from '@/lib/auth';

function ReadingPhaseContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [problem, setProblem] = useState<Problem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const hasLoadedRef = useRef(false);
  
  // Get selected task type from URL params
  const selectedTask = searchParams.get('task') || 'task3';

  // Load or generate problem
  useEffect(() => {
    // Prevent duplicate execution in React Strict Mode
    if (hasLoadedRef.current) {
      return;
    }

    const loadProblem = async () => {
      try {
        // Check if user is logged in
        const userIdentifier = getUserIdentifier();
        if (!userIdentifier) {
          console.warn('⚠️ User not logged in, redirecting to login page');
          setError('ログインが必要です。ログインページに移動します。');
          setTimeout(() => {
            router.push('/login');
          }, 2000);
          setIsLoading(false);
          return;
        }

        console.log('✅ User logged in:', userIdentifier);

        // Check if problem data is passed via URL params
        const problemData = searchParams.get('problem');
        const isMockExam = searchParams.get('mockExam') === 'true';

        if (problemData && problemData !== 'undefined') {
          // Use existing problem data from URL
          console.log('📖 Using existing problem from URL params');
          const parsedProblem = JSON.parse(decodeURIComponent(problemData));
          setProblem(parsedProblem);
          // Store in session storage for later use
          sessionStorage.setItem('currentProblem', JSON.stringify(parsedProblem));
          hasLoadedRef.current = true;
        } else if (isMockExam) {
          // For mock exam, try to get problem from sessionStorage
          console.log('🎯 Mock exam mode: checking sessionStorage for problem...');
          const storedProblem = sessionStorage.getItem('currentProblem');
          if (storedProblem) {
            const parsedProblem = JSON.parse(storedProblem);
            setProblem(parsedProblem);
            hasLoadedRef.current = true;
            console.log('📖 Using problem from sessionStorage:', parsedProblem.problem_id);
          } else {
            throw new Error('Mock exam problem not found in sessionStorage');
          }
        } else {
          // Generate new problem for regular practice
          console.log('🎲 Generating new problem...');
          const newProblem = await generateProblem(userIdentifier, selectedTask);
          console.log('✅ Problem generated:', newProblem.problem_id);
          setProblem(newProblem);
          // Store in session storage for later use
          sessionStorage.setItem('currentProblem', JSON.stringify(newProblem));
          hasLoadedRef.current = true;
        }
      } catch (err) {
        console.error('❌ Failed to load problem:', err);
        setError('問題の読み込みに失敗しました。ホームに戻ってもう一度お試しください。');
      } finally {
        setIsLoading(false);
      }
    };

    loadProblem();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 空の依存配列でマウント時のみ実行

  // Handle timer completion - transition to Listening Phase
  const handleTimerComplete = () => {
    if (problem) {
      // Check if this is a mock exam
      const isMockExam = searchParams.get('mockExam') === 'true';
      const mockExamParam = isMockExam ? '&mockExam=true' : '';
      
      // Navigate to listening phase with problem data and task type
      const problemParam = encodeURIComponent(JSON.stringify(problem));
      router.push(`/practice/listening?problem=${problemParam}&task=${selectedTask}${mockExamParam}`);
    }
  };

  const handleBackToHome = () => {
    router.push('/home');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--background)' }}>
        <div className="max-w-md mx-auto px-4 text-center">
          <div className="luxury-card rounded-2xl p-10">
            <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6" style={{
              background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%)',
              border: '1px solid var(--border-color-gold)'
            }}>
              <svg className="w-10 h-10 gold-accent animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <h2 className="text-2xl font-bold mb-3 gold-accent">問題を生成中</h2>
            <p className="mb-2 font-light" style={{ color: 'var(--foreground-muted)' }}>
              AIが問題と音声を生成しています
            </p>
            <p className="text-sm font-light" style={{ color: 'var(--foreground-muted)' }}>
              少々お待ちください（5-10秒程度）
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !problem) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--background)' }}>
        <div className="max-w-md mx-auto px-4 text-center">
          <div className="luxury-card rounded-2xl p-10">
            <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6" style={{
              background: 'rgba(220, 38, 38, 0.1)',
              border: '1px solid rgba(220, 38, 38, 0.3)'
            }}>
              <svg className="w-10 h-10" style={{ color: '#fca5a5' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold mb-3" style={{ color: 'var(--foreground)' }}>エラー</h2>
            <p className="mb-8 font-light" style={{ color: 'var(--foreground-muted)' }}>{error}</p>
            <button
              onClick={handleBackToHome}
              className="btn-luxury w-full py-4 px-6 rounded-xl font-semibold tracking-wide"
            >
              ホームに戻る
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen fade-enter" style={{ background: 'var(--background)' }}>
      {/* Header */}
      <header className="surface-elevated backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <h1 className="text-xl sm:text-2xl font-bold gold-accent">
                {selectedTask.toUpperCase()} - Reading Phase
              </h1>
              {searchParams.get('mockExam') === 'true' && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  模擬試験
                </span>
              )}
            </div>
            <button
              onClick={handleBackToHome}
              className="text-sm hover:text-luxury transition-all duration-300"
              style={{ color: 'var(--foreground-muted)' }}
            >
              中止
            </button>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="surface-elevated">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold gold-accent tracking-wide">{selectedTask.toUpperCase()} - Reading</span>
            <span className="text-sm font-light" style={{ color: 'var(--foreground-muted)' }}>1 / 4</span>
          </div>
          <div className="w-full rounded-full h-1.5" style={{ background: 'var(--background-elevated)' }}>
            <div
              className="gold-gradient h-1.5 rounded-full transition-all duration-300"
              style={{ width: '25%' }}
            />
          </div>
        </div>
      </div>

      {/* Main Content - Responsive */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
        {/* Timer Section - Responsive */}
        <div className="luxury-card rounded-2xl p-6 sm:p-8 mb-6 sm:mb-8">
          <div className="text-center">
            <p className="text-sm font-light tracking-wide mb-4" style={{ color: 'var(--foreground-muted)' }}>残り時間</p>
            <Timer
              duration={45}
              onComplete={handleTimerComplete}
              warningThreshold={15}
            />
          </div>
        </div>

        {/* Reading Material - Responsive */}
        <div className="luxury-card rounded-2xl p-6 sm:p-8 lg:p-10">
          <div className="mb-6">
            <h2 className="text-lg sm:text-xl md:text-2xl font-bold mb-3 gold-accent">
              {selectedTask === 'task2' ? 'University Announcement' : 'Reading Passage'}
            </h2>
            <p className="text-sm font-light tracking-wide" style={{ color: 'var(--foreground-muted)' }}>
              {selectedTask === 'task2' 
                ? '以下の大学からのアナウンスを45秒間で読んでください。' 
                : '以下の文章を45秒間で読んでください。'
              }
            </p>
          </div>

          <div className="prose prose-sm sm:prose max-w-none">
            <div className="text-sm sm:text-base leading-relaxed whitespace-pre-wrap font-light" style={{ color: 'var(--foreground)' }}>
              {problem.reading_text}
            </div>
          </div>

          {/* Topic Category Badge */}
          <div className="mt-6 sm:mt-8 pt-6" style={{ borderTop: '1px solid var(--border-color)' }}>
            <span className="inline-flex items-center px-4 py-2 rounded-full text-xs font-medium tracking-wide" style={{
              background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.05) 100%)',
              border: '1px solid var(--border-color-gold)',
              color: 'var(--color-accent-gold)'
            }}>
              {problem.topic_category}
            </span>
          </div>
        </div>

        {/* Instructions - Responsive */}
        <div className="mt-6 sm:mt-8 rounded-xl p-4 sm:p-5" style={{
          background: 'rgba(212, 175, 55, 0.05)',
          border: '1px solid var(--border-color-gold)'
        }}>
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 gold-accent" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-light tracking-wide" style={{ color: 'var(--foreground-muted)' }}>
                タイマーが終了すると、自動的に次のフェーズ（Listening）に進みます。
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function ReadingPhasePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--background)' }}>
        <LoadingSpinner />
      </div>
    }>
      <ReadingPhaseContent />
    </Suspense>
  );
}
