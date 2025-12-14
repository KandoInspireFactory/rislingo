/**
 * Results Page - Displays scoring results after Speaking Phase
 * 
 * Features:
 * - Fetches and displays scoring results
 * - Shows overall score and detailed feedback
 * - Provides navigation options
 * 
 * Requirements: 5.2, 5.4
 */

'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import ScoreDisplay from '@/components/ScoreDisplay';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorScreen from '@/components/ErrorScreen';
import { ScoringResponse } from '@/lib/types';

function ResultsContent() {
  const searchParams = useSearchParams();
  const [scoringResult, setScoringResult] = useState<ScoringResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Get selected task type from URL params
  const selectedTask = searchParams.get('task') || 'task3';

  useEffect(() => {
    // Try to get scoring result from session storage
    const storedResult = sessionStorage.getItem('scoringResult');
    
    if (storedResult) {
      try {
        const result = JSON.parse(storedResult);
        console.log('✅ Scoring result loaded from session storage');
        setScoringResult(result);
        setIsLoading(false);
      } catch (err) {
        console.error('❌ Failed to parse scoring result:', err);
        setError('採点結果の読み込みに失敗しました。');
        setIsLoading(false);
      }
    } else {
      console.error('❌ No scoring result found in session storage');
      setError('採点結果が見つかりません。もう一度練習してください。');
      setIsLoading(false);
    }
  }, [searchParams]);

  if (isLoading) {
    return <LoadingSpinner message="採点結果を読み込んでいます..." />;
  }

  if (error || !scoringResult) {
    return <ErrorScreen error={error || '採点結果が見つかりません。'} />;
  }

  return <ScoreDisplay scoringResult={scoringResult} taskType={selectedTask} />;
}

export default function ResultsPage() {
  return (
    <Suspense fallback={<LoadingSpinner message="採点結果を読み込んでいます..." />}>
      <ResultsContent />
    </Suspense>
  );
}
