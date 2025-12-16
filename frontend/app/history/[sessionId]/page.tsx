'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { isAuthenticated, getUserIdentifier } from '@/lib/auth';
import { fetchSessionDetail } from '@/lib/api-client';
import { SessionDetailResponse } from '@/lib/types';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorScreen from '@/components/ErrorScreen';

export default function SessionDetailPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [session, setSession] = useState<SessionDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'problem' | 'response' | 'feedback' | 'model'>('feedback');
  const router = useRouter();
  const params = useParams();
  const sessionId = params.sessionId as string;

  useEffect(() => {
    const loadSessionDetail = async () => {
      const authenticated = await isAuthenticated();
      if (!authenticated) {
        router.push('/login');
        return;
      }

      try {
        const userIdentifier = getUserIdentifier();
        if (!userIdentifier) {
          throw new Error('User identifier not found');
        }

        const sessionData = await fetchSessionDetail(sessionId, userIdentifier);
        setSession(sessionData);
      } catch (err) {
        console.error('Failed to load session detail:', err);
        setError('学習履歴の詳細を読み込めませんでした。');
      } finally {
        setIsLoading(false);
      }
    };

    loadSessionDetail();
  }, [sessionId, router]);

  const handleBack = () => {
    router.push('/home');
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error || !session) {
    return (
      <ErrorScreen
        error={error || '学習履歴が見つかりませんでした。'}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={handleBack}
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
              学習履歴詳細
            </h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Session Info */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="flex flex-wrap items-center gap-4 mb-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800">
              {session.task_type.toUpperCase()}
            </span>
            <span className="text-sm text-gray-500">
              {formatDate(session.created_at)}
            </span>
          </div>

          {/* Scores */}
          {session.overall_score !== null && (
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">総合スコア</div>
                <div className={`text-3xl font-bold ${getScoreColor(session.overall_score ?? 0)}`}>
                  {session.overall_score}/4
                </div>
              </div>
              {session.delivery_score !== null && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Delivery</div>
                  <div className={`text-2xl font-semibold ${getScoreColor(session.delivery_score ?? 0)}`}>
                    {session.delivery_score}/4
                  </div>
                </div>
              )}
              {session.language_use_score !== null && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Language Use</div>
                  <div className={`text-2xl font-semibold ${getScoreColor(session.language_use_score ?? 0)}`}>
                    {session.language_use_score}/4
                  </div>
                </div>
              )}
              {session.topic_dev_score !== null && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Topic Dev.</div>
                  <div className={`text-2xl font-semibold ${getScoreColor(session.topic_dev_score ?? 0)}`}>
                    {session.topic_dev_score}/4
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px overflow-x-auto">
              <button
                onClick={() => setActiveTab('problem')}
                className={`px-6 py-4 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                  activeTab === 'problem'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                問題
              </button>
              <button
                onClick={() => setActiveTab('response')}
                className={`px-6 py-4 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                  activeTab === 'response'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                あなたの回答
              </button>
              <button
                onClick={() => setActiveTab('feedback')}
                className={`px-6 py-4 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                  activeTab === 'feedback'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                フィードバック
              </button>
              {session.model_answer && (
                <button
                  onClick={() => setActiveTab('model')}
                  className={`px-6 py-4 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                    activeTab === 'model'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  模範解答
                </button>
              )}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'problem' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Reading</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-gray-700 whitespace-pre-wrap">{session.reading_text}</p>
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Lecture Script</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-gray-700 whitespace-pre-wrap">{session.lecture_script}</p>
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Question</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-gray-700 whitespace-pre-wrap">{session.question}</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'response' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">あなたの回答</h3>
                {session.user_transcript ? (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-gray-700 whitespace-pre-wrap">{session.user_transcript}</p>
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">回答が記録されていません。</p>
                )}
              </div>
            )}

            {activeTab === 'feedback' && (
              <div className="space-y-6">
                {session.feedback ? (
                  <>
                    {session.feedback.delivery && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          Delivery ({session.feedback.delivery.score}/4)
                        </h3>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-gray-700">{session.feedback.delivery.feedback}</p>
                        </div>
                      </div>
                    )}
                    {session.feedback.language_use && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          Language Use ({session.feedback.language_use.score}/4)
                        </h3>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-gray-700">{session.feedback.language_use.feedback}</p>
                        </div>
                      </div>
                    )}
                    {session.feedback.topic_development && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          Topic Development ({session.feedback.topic_development.score}/4)
                        </h3>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-gray-700">{session.feedback.topic_development.feedback}</p>
                        </div>
                      </div>
                    )}
                    {session.feedback.improvement_tips && session.feedback.improvement_tips.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">改善アドバイス</h3>
                        <div className="bg-blue-50 rounded-lg p-4">
                          <ul className="list-disc list-inside space-y-2">
                            {session.feedback.improvement_tips.map((tip, index) => (
                              <li key={index} className="text-gray-700">{tip}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-gray-500 text-center py-8">フィードバックがありません。</p>
                )}
              </div>
            )}

            {activeTab === 'model' && session.model_answer && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">模範解答</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-gray-700 whitespace-pre-wrap">{session.model_answer}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex flex-col sm:flex-row gap-4">
          <button
            onClick={() => router.push('/practice/reading')}
            className="flex-1 bg-indigo-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
          >
            もう一度練習
          </button>
          <button
            onClick={handleBack}
            className="flex-1 bg-white text-gray-700 px-6 py-3 rounded-lg font-medium border border-gray-300 hover:bg-gray-50 transition-colors"
          >
            ホームに戻る
          </button>
        </div>
      </main>
    </div>
  );
}

/**
 * Format date string to Japanese locale.
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Get color class based on score value.
 */
function getScoreColor(score: number): string {
  if (score >= 3.5) return 'text-green-600';
  if (score >= 2.5) return 'text-blue-600';
  if (score >= 1.5) return 'text-yellow-600';
  return 'text-red-600';
}
