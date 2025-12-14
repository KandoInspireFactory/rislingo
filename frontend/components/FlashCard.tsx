'use client';

import { useState } from 'react';
import { SavedPhrase } from '@/lib/types';

interface FlashCardProps {
  phrase: SavedPhrase;
  onMastered: () => void;
  onNotYet: () => void;
}

/**
 * FlashCard component for displaying and reviewing saved phrases.
 * Implements card flip animation and mastery tracking.
 */
export default function FlashCard({ phrase, onMastered, onNotYet }: FlashCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="w-full max-w-2xl mx-auto px-4 sm:px-6">
      {/* Card Container with 3D flip effect */}
      <div 
        className={`flip-card ${isFlipped ? 'flipped' : ''}`}
        onClick={handleFlip}
        style={{ 
          height: '400px',
          cursor: 'pointer',
          perspective: '1000px'
        }}
      >
        <div className="flip-card-inner">
          {/* Front of Card */}
          <div className="flip-card-front bg-white rounded-2xl shadow-xl p-6 sm:p-8 flex flex-col items-center justify-center">
            <div className="text-center">
              <p className="text-xl sm:text-2xl md:text-3xl font-semibold text-gray-900 mb-4 px-4">
                {phrase.phrase}
              </p>
              <p className="text-xs sm:text-sm text-gray-500 mt-8">
                タップしてめくる
              </p>
            </div>
          </div>

          {/* Back of Card */}
          <div className="flip-card-back bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl shadow-xl p-6 sm:p-8">
            <div className="h-full flex flex-col">
              <div className="flex-1 overflow-y-auto">
                {/* Context/Usage Example */}
                {phrase.context && (
                  <div className="mb-4 sm:mb-6">
                    <h3 className="text-xs sm:text-sm font-semibold text-gray-700 mb-2">
                      使用例
                    </h3>
                    <p className="text-sm sm:text-base text-gray-800 leading-relaxed">
                      {phrase.context}
                    </p>
                  </div>
                )}

                {/* Category */}
                {phrase.category && (
                  <div className="mb-4 sm:mb-6">
                    <h3 className="text-xs sm:text-sm font-semibold text-gray-700 mb-2">
                      カテゴリ
                    </h3>
                    <span className="inline-block px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-xs sm:text-sm">
                      {phrase.category}
                    </span>
                  </div>
                )}

                {/* Saved Date */}
                <div className="mb-4">
                  <h3 className="text-xs sm:text-sm font-semibold text-gray-700 mb-2">
                    保存日
                  </h3>
                  <p className="text-xs sm:text-sm text-gray-600">
                    {formatDate(phrase.created_at)}
                  </p>
                </div>
              </div>

              <p className="text-xs text-gray-500 text-center mt-4">
                タップして戻る
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons - Responsive */}
      <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mt-6 max-w-md mx-auto">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onNotYet();
          }}
          className="flex-1 px-4 sm:px-6 py-2.5 sm:py-3 bg-gray-200 text-gray-800 rounded-lg text-sm sm:text-base font-semibold hover:bg-gray-300 transition-colors"
        >
          まだ
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onMastered();
          }}
          className="flex-1 px-4 sm:px-6 py-2.5 sm:py-3 bg-green-500 text-white rounded-lg text-sm sm:text-base font-semibold hover:bg-green-600 transition-colors"
        >
          覚えた
        </button>
      </div>
    </div>
  );
}
