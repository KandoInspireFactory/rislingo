/**
 * Preparation Phase - Task 3 Practice Flow
 * 
 * Features:
 * - 30-second countdown timer
 * - Display question text
 * - Simple note-taking area
 * - Auto-transition to Speaking Phase when timer completes
 * 
 * Requirements: 3.3
 */

'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Timer from '@/components/Timer';
import LoadingSpinner from '@/components/LoadingSpinner';
import PracticeLayout from '@/components/PracticeLayout';
import ErrorScreen from '@/components/ErrorScreen';
import { useProblemData } from '@/hooks/useProblemData';

function PreparationPhaseContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { problem, isLoading, error } = useProblemData();
  const [notes, setNotes] = useState('');
  
  // Get selected task type from URL params (will be passed through from previous phases)
  const selectedTask = searchParams.get('task') || 'task3';
  
  // Set preparation time based on task type
  const preparationTime = selectedTask === 'task1' ? 15 : selectedTask === 'task4' ? 20 : 30;

  // Handle timer completion - transition to Speaking Phase
  const handleTimerComplete = () => {
    if (problem) {
      // Check if this is a mock exam
      const isMockExam = searchParams.get('mockExam') === 'true';
      const mockExamParam = isMockExam ? '&mockExam=true' : '';
      
      // Navigate to speaking phase with problem data and task type
      const problemParam = encodeURIComponent(JSON.stringify(problem));
      router.push(`/practice/speaking?problem=${problemParam}&task=${selectedTask}${mockExamParam}`);
    }
  };

  // Show loading screen
  if (isLoading) {
    return <ErrorScreen error="" showLoading />;
  }

  // Show error screen
  if (error || !problem) {
    return <ErrorScreen error={error || '不明なエラーが発生しました。'} />;
  }

  const isMockExam = searchParams.get('mockExam') === 'true';

  return (
    <PracticeLayout phase="Preparation" phaseNumber={3} taskType={selectedTask} isMockExam={isMockExam}>
      <div className="fade-enter">
        {/* Timer Section */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-4">準備時間</p>
            <Timer 
              duration={preparationTime} 
              onComplete={handleTimerComplete}
              warningThreshold={Math.floor(preparationTime / 2)}
            />
          </div>
        </div>

        {/* Question Section */}
        <div className="bg-white rounded-xl shadow-md p-6 sm:p-8 mb-6">
          <div className="mb-4">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">
              Question
            </h2>
            <p className="text-sm text-gray-600">
              以下の質問に答える準備をしてください。
            </p>
          </div>
          
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 sm:p-6">
            <p className="text-gray-800 leading-relaxed">
              {problem.question}
            </p>
          </div>
        </div>

        {/* Notes Section */}
        <div className="bg-white rounded-xl shadow-md p-6 sm:p-8 mb-6">
          <div className="mb-4">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">
              メモ（オプション）
            </h2>
            <p className="text-sm text-gray-600">
              回答の準備にメモを取ることができます。
            </p>
          </div>
          
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="ここにメモを入力してください..."
            className="w-full h-40 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none text-gray-800 placeholder-gray-400"
            aria-label="Notes area"
          />
          
          <div className="mt-2 text-xs text-gray-500">
            {notes.length} 文字
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                タイマーが終了すると、自動的に次のフェーズ（Speaking）に進みます。
              </p>
            </div>
          </div>
        </div>
      </div>
      </PracticeLayout>
  );
}

export default function PreparationPhasePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    }>
      <PreparationPhaseContent />
    </Suspense>
  );
}
