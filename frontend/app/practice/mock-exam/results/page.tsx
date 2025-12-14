'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import LoadingSpinner from '@/components/LoadingSpinner';
import BackButton from '@/components/BackButton';

interface TaskResult {
  taskNumber: number;
  problem: any;
  transcript: string;
  score: number;
  feedback?: any;
}

interface MockExamResults {
  taskResults: TaskResult[];
  totalScore: number;
  scaledScore: number; // Out of 30
  isLoading: boolean;
}

export default function MockExamResultsPage() {
  const [results, setResults] = useState<MockExamResults>({
    taskResults: [],
    totalScore: 0,
    scaledScore: 0,
    isLoading: true
  });
  const router = useRouter();

  useEffect(() => {
    const processResults = async () => {
      try {
        // Get mock exam data from session storage
        const mockExamData = sessionStorage.getItem('mockExamResults');
        if (!mockExamData) {
          console.error('No mock exam results found');
          router.push('/practice/select');
          return;
        }

        const examData = JSON.parse(mockExamData);
        console.log('📊 Processing mock exam results:', examData);

        // Score all tasks
        const taskResults: TaskResult[] = [];
        let totalScore = 0;

        for (let i = 0; i < examData.problems.length; i++) {
          const problem = examData.problems[i];
          const transcript = examData.transcripts[i];
          const taskNumber = i + 1;

          console.log(`🎯 Scoring Task ${taskNumber}...`);

          let score = 0;
          let feedback = null;

          try {
            if (taskNumber === 1) {
              // Score Task 1
              const { evaluateTask1Response } = await import('@/lib/api-client');
              const result = await evaluateTask1Response({
                problem_id: problem.problem_id,
                transcript: transcript,
                question: problem.question
              });
              score = result.overall_score;
              feedback = result;
            } else {
              // Score Task 2, 3, 4
              const { evaluateResponse } = await import('@/lib/api-client');
              const result = await evaluateResponse({
                problem_id: problem.problem_id,
                transcript: transcript,
                reading_text: problem.reading_text,
                lecture_script: problem.lecture_script
              });
              score = result.overall_score;
              feedback = result;
            }
          } catch (error) {
            console.error(`❌ Failed to score Task ${taskNumber}:`, error);
            score = 0; // Default to 0 if scoring fails
          }

          taskResults.push({
            taskNumber,
            problem,
            transcript,
            score,
            feedback
          });

          totalScore += score;
          console.log(`✅ Task ${taskNumber} scored: ${score}/4`);
        }

        // Calculate scaled score (TOEFL formula: total/4 * 7.6, rounded down)
        const scaledScore = Math.floor((totalScore / 4) * 7.6);

        setResults({
          taskResults,
          totalScore,
          scaledScore,
          isLoading: false
        });

        console.log(`🎉 Mock exam scoring complete: ${totalScore}/16 (${scaledScore}/30)`);

        // Clean up session storage
        sessionStorage.removeItem('mockExamResults');
        sessionStorage.removeItem('mockExamState');
        sessionStorage.removeItem('isMockExam');

      } catch (error) {
        console.error('❌ Error processing mock exam results:', error);
        alert('結果の処理中にエラーが発生しました。');
        router.push('/practice/select');
      }
    };

    processResults();
  }, [router]);

  if (results.isLoading) {
    return (
      <div className="min-h-screen" style={{ background: 'var(--background)' }}>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <LoadingSpinner message="模擬試験を採点しています..." />
            <p className="text-sm mt-4" style={{ color: 'var(--foreground-muted)' }}>
              全4タスクの採点を行っています（30-60秒程度）
            </p>
          </div>
        </div>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-600';
    if (score >= 3) return 'text-blue-600';
    if (score >= 2) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score: number) => {
    switch (score) {
      case 4: return '優秀';
      case 3: return '良好';
      case 2: return '改善必要';
      case 1: return '要練習';
      default: return '未回答';
    }
  };

  return (
    <div className="min-h-screen" style={{ background: 'var(--background)' }}>
      {/* Header */}
      <header className="surface-elevated backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex items-center gap-4">
          <BackButton />
          <h1 className="text-xl sm:text-2xl font-bold text-luxury">
            模擬試験結果
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Overall Score */}
        <div className="surface-card rounded-2xl p-8 mb-8 text-center">
          <h2 className="text-3xl font-bold mb-4" style={{ color: 'var(--foreground)' }}>
            総合スコア
          </h2>
          <div className="flex items-center justify-center gap-8 mb-6">
            <div>
              <div className="text-5xl font-bold text-luxury mb-2">
                {results.scaledScore}
              </div>
              <div className="text-lg" style={{ color: 'var(--foreground-muted)' }}>
                / 30点
              </div>
            </div>
            <div className="text-2xl" style={{ color: 'var(--foreground-muted)' }}>
              ({results.totalScore}/16)
            </div>
          </div>
          <p className="text-lg" style={{ color: 'var(--foreground-muted)' }}>
            TOEFL iBT Speaking セクション換算スコア
          </p>
        </div>

        {/* Task Breakdown */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {results.taskResults.map((result) => (
            <div key={result.taskNumber} className="surface-card rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold">
                  Task {result.taskNumber}
                </h3>
                <div className={`text-2xl font-bold ${getScoreColor(result.score)}`}>
                  {result.score}/4
                </div>
              </div>
              
              <div className="mb-4">
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(result.score)} bg-opacity-10`}>
                  {getScoreLabel(result.score)}
                </span>
              </div>

              {result.feedback && (
                <div className="space-y-3">
                  {result.taskNumber === 1 ? (
                    // Task 1 feedback
                    <div className="space-y-2">
                      <div className="text-sm">
                        <strong>発話:</strong> {result.feedback.delivery_feedback}
                      </div>
                      <div className="text-sm">
                        <strong>言語使用:</strong> {result.feedback.language_use_feedback}
                      </div>
                      <div className="text-sm">
                        <strong>内容展開:</strong> {result.feedback.topic_dev_feedback}
                      </div>
                    </div>
                  ) : (
                    // Task 2, 3, 4 feedback
                    <div className="space-y-2">
                      <div className="text-sm">
                        <strong>発話:</strong> {result.feedback.delivery?.feedback}
                      </div>
                      <div className="text-sm">
                        <strong>言語使用:</strong> {result.feedback.language_use?.feedback}
                      </div>
                      <div className="text-sm">
                        <strong>内容展開:</strong> {result.feedback.topic_development?.feedback}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Score Interpretation */}
        <div className="surface-card rounded-xl p-6 mb-8">
          <h3 className="text-xl font-bold mb-4">スコア解釈</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-2">TOEFL iBT Speaking スコア範囲</h4>
              <ul className="space-y-1 text-sm">
                <li><span className="text-green-600">●</span> 26-30: 優秀 (Advanced)</li>
                <li><span className="text-blue-600">●</span> 18-25: 良好 (High-Intermediate)</li>
                <li><span className="text-yellow-600">●</span> 10-17: 中級 (Low-Intermediate)</li>
                <li><span className="text-red-600">●</span> 0-9: 初級 (Novice)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">各タスクの採点基準</h4>
              <ul className="space-y-1 text-sm">
                <li><strong>4点:</strong> 英語の表現がよく、構成も回答もよい</li>
                <li><strong>3点:</strong> 英語の間違いは散見しつつも、テンポと構成よく問に答えきれている</li>
                <li><strong>2点:</strong> 英語の間違いが散見しつつ、テンポと構成がまずく問に答えきれていない</li>
                <li><strong>1点:</strong> ほとんど話していない</li>
                <li><strong>0点:</strong> 全く話していない</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => router.push('/practice/select')}
            className="btn-primary"
          >
            新しい練習を始める
          </button>
          <button
            onClick={() => router.push('/dashboard')}
            className="btn-secondary"
          >
            ダッシュボードに戻る
          </button>
        </div>
      </main>
    </div>
  );
}