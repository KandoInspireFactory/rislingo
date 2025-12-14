'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';
import LoadingSpinner from '@/components/LoadingSpinner';
import TaskSelectionCard from '@/components/TaskSelectionCard';
import BackButton from '@/components/BackButton';

export default function PracticeSelectPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingTask, setGeneratingTask] = useState<string | null>(null);
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

  const handleTaskSelect = async (taskType: string) => {
    if (taskType === 'mock-exam') {
      // 模擬試験の場合は特別な処理
      router.push('/practice/mock-exam');
      return;
    }

    if (taskType === 'task1') {
      // Task1の場合は問題生成してからPreparationフェーズに移行
      await generateTask1Problem();
    } else if (taskType === 'task4') {
      // Task4はReadingがないため、ここで問題を生成して直接Listeningフェーズへ
      await generateTask4Problem();
    } else {
      // Task2, Task3の場合はReadingフェーズから開始
      router.push(`/practice/reading?task=${taskType}`);
    }
  };

  const generateTask1Problem = async () => {
    setIsGenerating(true);
    setGeneratingTask('task1');

    try {
      // Import API function dynamically
      const { generateProblem } = await import('@/lib/api-client');
      const { getUserIdentifier } = await import('@/lib/auth');

      // Get user identifier
      const userIdentifier = getUserIdentifier();
      if (!userIdentifier) {
        throw new Error('ログインが必要です。');
      }

      console.log('🎲 Generating Task 1 problem...');
      
      // Generate Task 1 problem
      const problem = await generateProblem(userIdentifier, 'task1');
      
      console.log('✅ Task 1 problem generated:', problem.problem_id);
      
      // Store problem data in session storage
      sessionStorage.setItem('currentProblem', JSON.stringify(problem));
      
      // Navigate to preparation phase
      router.push(`/practice/preparation?task=task1`);
      
    } catch (error) {
      console.error('❌ Task 1 problem generation failed:', error);
      
      // Show error message
      alert(error instanceof Error ? error.message : 'Task1の問題生成に失敗しました。もう一度お試しください。');
    } finally {
      setIsGenerating(false);
      setGeneratingTask(null);
    }
  };

  const generateTask4Problem = async () => {
    setIsGenerating(true);
    setGeneratingTask('task4');

    try {
      const { generateProblem } = await import('@/lib/api-client');
      const { getUserIdentifier } = await import('@/lib/auth');

      const userIdentifier = getUserIdentifier();
      if (!userIdentifier) {
        throw new Error('ログインが必要です。');
      }

      console.log('🎲 Generating Task 4 problem...');
      const problem = await generateProblem(userIdentifier, 'task4');

      console.log('✅ Task 4 problem generated:', problem.problem_id);
      // Store problem data in session storage
      sessionStorage.setItem('currentProblem', JSON.stringify(problem));

      // Navigate directly to listening phase with problem data in query
      const problemParam = encodeURIComponent(JSON.stringify(problem));
      router.push(`/practice/listening?problem=${problemParam}&task=task4`);

    } catch (error) {
      console.error('❌ Task 4 problem generation failed:', error);
      alert(error instanceof Error ? error.message : 'Task4の問題生成に失敗しました。もう一度お試しください。');
    } finally {
      setIsGenerating(false);
      setGeneratingTask(null);
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (isGenerating) {
    return (
      <div className="min-h-screen" style={{ background: 'var(--background)' }}>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <LoadingSpinner message={`${generatingTask?.toUpperCase()}の問題を生成しています...`} />
            <p className="text-sm mt-4" style={{ color: 'var(--foreground-muted)' }}>
              AIが問題を作成中です（5-10秒程度）
            </p>
          </div>
        </div>
      </div>
    );
  }

  const tasks = [
    {
      id: 'task1',
      title: 'Task 1',
      description: '自分の意見と理由を即興で述べる独立型スピーキング',
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    },
    {
      id: 'task2',
      title: 'Task 2',
      description: 'キャンパスの変更案に対する学生の意見と理由を要約',
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
        </svg>
      )
    },
    {
      id: 'task3',
      title: 'Task 3',
      description: '学術用語の定義と教授の具体例を説明する課題',
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      )
    },
    {
      id: 'task4',
      title: 'Task 4',
      description: '講義内容の要点と例を整理して要約する課題',
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
        </svg>
      )
    },
    {
      id: 'mock-exam',
      title: '模擬試験',
      description: '本番形式での総合練習 - 全タスクを連続で実施',
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      isSpecial: true
    }
  ];

  return (
    <div className="min-h-screen" style={{ background: 'var(--background)' }}>
      {/* Header */}
      <header className="surface-elevated backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex items-center gap-4">
          <BackButton />
          <h1 className="text-xl sm:text-2xl font-bold text-luxury">
            練習タスクを選択
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
        {/* Title Section */}
        <div className="text-center mb-12 sm:mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4 sm:mb-6" style={{ color: 'var(--foreground)' }}>
            どのタスクで練習しますか？
          </h2>
          <p className="text-lg sm:text-xl gold-accent font-light tracking-wide">
            練習したいタスクを選択してください
          </p>
        </div>

        {/* Task Selection Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8 max-w-6xl mx-auto">
          {tasks.map((task) => (
            <TaskSelectionCard
              key={task.id}
              task={task}
              onSelect={() => handleTaskSelect(task.id)}
              isGenerating={isGenerating && generatingTask === task.id}
              disabled={isGenerating}
            />
          ))}
        </div>
      </main>
    </div>
  );
}