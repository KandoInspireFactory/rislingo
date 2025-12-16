'use client';

import { useState } from 'react';
import type { Task1Question } from '@/lib/types';

interface Task1QuestionCardProps {
  question: Task1Question;
  onNext: () => void;
  onPrevious: () => void;
  canGoNext: boolean;
  canGoPrevious: boolean;
}

/**
 * Task1QuestionCard component for displaying Task1 questions in a flashcard-like interface.
 * Shows question on front, user response and score on back.
 */
export default function Task1QuestionCard({ 
  question, 
  onNext, 
  onPrevious, 
  canGoNext, 
  canGoPrevious 
}: Task1QuestionCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getScoreColor = (score?: number) => {
    if (!score && score !== 0) return 'text-gray-500';
    if (score >= 4) return 'text-green-600';
    if (score >= 3) return 'text-blue-600';
    if (score >= 2) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score?: number) => {
    if (!score && score !== 0) return '未採点';
    switch (score) {
      case 4: return '優秀';
      case 3: return '良好';
      case 2: return '改善必要';
      case 1: return '要練習';
      default: return '未回答';
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6">
      {/* Card Container with 3D flip effect */}
      <div 
        className={`flip-card ${isFlipped ? 'flipped' : ''}`}
        onClick={handleFlip}
        style={{ 
          height: '500px',
          cursor: 'pointer',
          perspective: '1000px'
        }}
      >
        <div className="flip-card-inner">
          {/* Front of Card - Question */}
          <div className="flip-card-front surface-card rounded-2xl p-6 sm:p-8 flex flex-col">
            <div className="flex-1 flex flex-col items-center justify-center">
              <div className="text-center max-w-3xl">
                <div className="mb-6">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                    Task 1 - Independent Speaking
                  </span>
                </div>
                <h2 className="text-xl sm:text-2xl md:text-3xl font-semibold mb-6" style={{ color: 'var(--foreground)' }}>
                  Question
                </h2>
                <p className="text-base sm:text-lg md:text-xl leading-relaxed" style={{ color: 'var(--foreground)' }}>
                  {question.question}
                </p>
              </div>
            </div>
            <div className="text-center mt-6">
              <p className="text-xs sm:text-sm" style={{ color: 'var(--foreground-muted)' }}>
                タップして回答を確認
              </p>
            </div>
          </div>

          {/* Back of Card - Response and Score */}
          <div className="flip-card-back surface-card rounded-2xl p-6 sm:p-8" style={{
            background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(147, 51, 234, 0.05) 100%)'
          }}>
            <div className="h-full flex flex-col">
              {/* Score Section */}
              <div className="text-center mb-6">
                <div className="flex items-center justify-center gap-4 mb-4">
                  <div className="text-center">
                    <div className={`text-3xl font-bold ${getScoreColor(question.overall_score ?? 0)}`}>
                      {question.overall_score !== undefined ? `${question.overall_score}/4` : '未採点'}
                    </div>
                    <div className={`text-sm font-medium ${getScoreColor(question.overall_score ?? 0)}`}>
                      Overall Score
                    </div>
                  </div>
                </div>
              </div>

              {/* Response Section */}
              <div className="flex-1 overflow-y-auto">
                <div className="mb-6">
                  <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--foreground)' }}>
                    あなたの回答
                  </h3>
                  {question.user_transcript ? (
                    <div className="surface-elevated rounded-lg p-4">
                      <p className="text-sm leading-relaxed" style={{ color: 'var(--foreground)' }}>
                        {question.user_transcript}
                      </p>
                    </div>
                  ) : (
                    <div className="surface-elevated rounded-lg p-4 text-center">
                      <p className="text-sm" style={{ color: 'var(--foreground-muted)' }}>
                        回答が記録されていません
                      </p>
                    </div>
                  )}
                </div>

                {/* Date */}
                <div className="mb-4">
                  <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--foreground)' }}>
                    実施日時
                  </h3>
                  <p className="text-sm" style={{ color: 'var(--foreground-muted)' }}>
                    {formatDate(question.created_at)}
                  </p>
                </div>
              </div>

              <div className="text-center mt-4">
                <p className="text-xs" style={{ color: 'var(--foreground-muted)' }}>
                  タップして問題に戻る
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between items-center mt-6 max-w-md mx-auto">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onPrevious();
          }}
          disabled={!canGoPrevious}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
            canGoPrevious 
              ? 'bg-blue-500 text-white hover:bg-blue-600' 
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          前へ
        </button>

        <div className="text-sm font-medium" style={{ color: 'var(--foreground-muted)' }}>
          {isFlipped ? '回答' : '問題'}
        </div>

        <button
          onClick={(e) => {
            e.stopPropagation();
            onNext();
          }}
          disabled={!canGoNext}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
            canGoNext 
              ? 'bg-blue-500 text-white hover:bg-blue-600' 
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          次へ
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}