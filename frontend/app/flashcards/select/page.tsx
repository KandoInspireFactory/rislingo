'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';
import LoadingSpinner from '@/components/LoadingSpinner';
import BackButton from '@/components/BackButton';

export default function FlashcardSelectPage() {
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      const authenticated = await isAuthenticated();
      if (!authenticated) {
        router.push('/login');
      } else {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [router]);

  const handleFlashcards = () => {
    // Navigate to the existing flashcard page
    router.push('/flashcards/review');
  };

  const handleTask1Archive = () => {
    // Navigate to Task1 archive page
    router.push('/flashcards/task1-archive');
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  const options = [
    {
      id: 'flashcards',
      title: 'フラッシュカード',
      description: 'フラッシュカードで復習',
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      ),
      onClick: handleFlashcards
    },
    {
      id: 'task1-archive',
      title: 'Task1過去問題',
      description: 'Task1の過去問題を確認・復習できます',
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      onClick: handleTask1Archive,
      isComingSoon: false
    }
  ];

  return (
    <div className="min-h-screen" style={{ background: 'var(--background)' }}>
      {/* Header */}
      <header className="surface-elevated backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex items-center gap-4">
          <BackButton />
          <h1 className="text-xl sm:text-2xl font-bold text-luxury">
            学習コンテンツを選択
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
        {/* Title Section */}
        <div className="text-center mb-12 sm:mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4 sm:mb-6" style={{ color: 'var(--foreground)' }}>
            どちらを利用しますか？
          </h2>
          <p className="text-lg sm:text-xl gold-accent font-light tracking-wide">
            学習したい内容を選択してください
          </p>
        </div>

        {/* Selection Cards */}
        <div className="grid sm:grid-cols-2 gap-6 sm:gap-8 max-w-5xl mx-auto">
          {options.map((option) => (
            <button
              key={option.id}
              onClick={option.onClick}
              className="luxury-card rounded-2xl p-8 sm:p-10 text-left group relative overflow-hidden transition-all duration-300 hover:scale-[1.02]"
              disabled={option.isComingSoon}
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-yellow-500/10 to-transparent rounded-full blur-2xl"></div>
              
              {option.isComingSoon && (
                <div className="absolute top-4 right-4">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    準備中
                  </span>
                </div>
              )}
              
              <div className="relative">
                <div className={`w-14 h-14 rounded-xl flex items-center justify-center mb-6 ${
                  option.id === 'flashcards' 
                    ? 'gold-gradient' 
                    : 'bg-gradient-to-br from-blue-500/20 to-blue-600/20 border border-blue-500/30'
                }`}>
                  <div className={option.id === 'flashcards' ? 'text-black' : 'text-blue-600'}>
                    {option.icon}
                  </div>
                </div>
                <h3 className="text-xl sm:text-2xl font-bold mb-3 gold-accent">
                  {option.title}
                </h3>
                <p className="text-sm sm:text-base font-light tracking-wide" style={{ color: 'var(--foreground-muted)' }}>
                  {option.description}
                </p>
                
                {option.isComingSoon && (
                  <div className="mt-4 text-xs" style={{ color: 'var(--foreground-muted)' }}>
                    この機能は近日公開予定です
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>

        {/* Info Section */}
        <div className="max-w-3xl mx-auto mt-12 sm:mt-16">
          <div className="surface-card rounded-xl p-6 sm:p-8">
            <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--foreground)' }}>
              学習コンテンツについて
            </h3>
            <div className="space-y-4 text-sm sm:text-base" style={{ color: 'var(--foreground-muted)' }}>
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full gold-gradient mt-2 flex-shrink-0"></div>
                <div>
                  <strong className="gold-accent">フラッシュカード:</strong> 
                  練習中に保存した有用なフレーズを復習できます。マスターしたフレーズは記録され、効率的な学習をサポートします。
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-blue-500 mt-2 flex-shrink-0"></div>
                <div>
                  <strong style={{ color: 'var(--foreground)' }}>Task1過去問題:</strong> 
                  過去に実施したTask1の問題と回答を確認できます。自分の成長を振り返り、弱点を把握するのに役立ちます。
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}