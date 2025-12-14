'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';
import LoadingSpinner from '@/components/LoadingSpinner';
import BackButton from '@/components/BackButton';

interface MockExamState {
  currentTask: number; // 1-4
  problems: any[];
  transcripts: string[];
  isGenerating: boolean;
  isCompleted: boolean;
}

export default function MockExamPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [examState, setExamState] = useState<MockExamState>({
    currentTask: 1,
    problems: [],
    transcripts: [],
    isGenerating: false,
    isCompleted: false
  });
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      const authenticated = await isAuthenticated();
      if (!authenticated) {
        router.push('/login');
      } else {
        setIsLoading(false);
        // Initialize mock exam
        await initializeMockExam();
      }
    };

    checkAuth();
  }, [router]);

  const initializeMockExam = async () => {
    setExamState(prev => ({ ...prev, isGenerating: true }));
    
    try {
      const { generateProblem } = await import('@/lib/api-client');
      const { getUserIdentifier } = await import('@/lib/auth');

      const userIdentifier = getUserIdentifier();
      if (!userIdentifier) {
        throw new Error('ログインが必要です。');
      }

      console.log('🎯 Generating mock exam problems...');
      
      // Generate problems for all 4 tasks
      const problems: any[] = [];
      const taskTypes = ['task1', 'task2', 'task3', 'task4'];
      
      for (let i = 0; i < taskTypes.length; i++) {
        const taskType = taskTypes[i];
        console.log(`🎲 Generating ${taskType} problem...`);
        
        try {
          const problem = await generateProblem(userIdentifier, taskType);
          problems.push(problem);
          console.log(`✅ ${taskType} problem generated successfully`);
        } catch (error) {
          console.error(`❌ Failed to generate ${taskType} problem:`, error);
          // For now, skip the failing task and continue with others
          // This is a temporary workaround for TTS issues
          console.log(`⚠️ Skipping ${taskType} due to generation error`);
          continue;
        }
      }
      
      if (problems.length === 0) {
        throw new Error('問題の生成に失敗しました。すべてのタスクで生成エラーが発生しています。');
      }
      
      console.log(`✅ Mock exam problems generated: ${problems.length}/4 tasks`);
      
      // Store problems and start with Task 1
      const newExamState = {
        ...examState,
        problems,
        isGenerating: false
      };
      
      setExamState(newExamState);
      
      // Start with the first available task
      const firstTaskIndex = taskTypes.findIndex(taskType => 
        problems.some(p => p.task_type === taskType)
      );
      
      if (firstTaskIndex !== -1) {
        const firstProblem = problems.find(p => p.task_type === taskTypes[firstTaskIndex]);
        startTaskWithState(firstTaskIndex + 1, firstProblem, newExamState);
      } else {
        throw new Error('利用可能な問題が見つかりませんでした。');
      }
      
    } catch (error) {
      console.error('❌ Mock exam initialization failed:', error);
      alert(error instanceof Error ? error.message : '模擬試験の初期化に失敗しました。');
      router.push('/practice/select');
    }
  };

  const startTask = (taskNumber: number, problem: any) => {
    startTaskWithState(taskNumber, problem, examState);
  };

  const startTaskWithState = (taskNumber: number, problem: any, state: MockExamState) => {
    console.log(`🚀 Starting Task ${taskNumber}`);
    console.log('📊 Exam state:', state);
    console.log('📝 Problem:', problem);
    
    // Store current problem and exam state
    sessionStorage.setItem('currentProblem', JSON.stringify(problem));
    sessionStorage.setItem('mockExamState', JSON.stringify(state));
    sessionStorage.setItem('isMockExam', 'true');
    
    // Navigate to appropriate phase based on task
    if (taskNumber === 1) {
      // Task 1: Direct to preparation
      router.push(`/practice/preparation?task=task1&mockExam=true`);
    } else if (taskNumber === 4) {
      // Task 4: Direct to listening (no reading)
      const problemParam = encodeURIComponent(JSON.stringify(problem));
      router.push(`/practice/listening?problem=${problemParam}&task=task4&mockExam=true`);
    } else {
      // Task 2, 3: Start with reading
      router.push(`/practice/reading?task=task${taskNumber}&mockExam=true`);
    }
  };

  if (isLoading || examState.isGenerating) {
    return (
      <div className="min-h-screen" style={{ background: 'var(--background)' }}>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <LoadingSpinner message="模擬試験を準備しています..." />
            <p className="text-sm mt-4" style={{ color: 'var(--foreground-muted)' }}>
              全4タスクの問題を生成中です（20-30秒程度）
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--background)' }}>
      {/* Header */}
      <header className="surface-elevated backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex items-center gap-4">
          <BackButton />
          <h1 className="text-xl sm:text-2xl font-bold text-luxury">
            TOEFL Speaking 模擬試験
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <div className="surface-card rounded-2xl p-8 mb-8">
            <h2 className="text-2xl font-bold mb-6" style={{ color: 'var(--foreground)' }}>
              模擬試験の準備が完了しました
            </h2>
            
            <div className="space-y-4 mb-8">
              <div className="flex items-center justify-between p-4 bg-opacity-50 rounded-lg" style={{ backgroundColor: 'var(--accent)' }}>
                <span className="font-medium">Task 1: Independent Speaking</span>
                <span className="text-sm" style={{ color: 'var(--foreground-muted)' }}>準備時間 15秒 / 回答時間 45秒</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-opacity-50 rounded-lg" style={{ backgroundColor: 'var(--accent)' }}>
                <span className="font-medium">Task 2: Campus Announcement</span>
                <span className="text-sm" style={{ color: 'var(--foreground-muted)' }}>読解 50秒 / 聴解 60-90秒 / 準備 30秒 / 回答 60秒</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-opacity-50 rounded-lg" style={{ backgroundColor: 'var(--accent)' }}>
                <span className="font-medium">Task 3: Campus Situation</span>
                <span className="text-sm" style={{ color: 'var(--foreground-muted)' }}>読解 50秒 / 聴解 60-90秒 / 準備 30秒 / 回答 60秒</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-opacity-50 rounded-lg" style={{ backgroundColor: 'var(--accent)' }}>
                <span className="font-medium">Task 4: Academic Course</span>
                <span className="text-sm" style={{ color: 'var(--foreground-muted)' }}>聴解 60-90秒 / 準備 20秒 / 回答 60秒</span>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-8">
              <p className="text-yellow-800 text-sm">
                <strong>注意:</strong> 模擬試験は本番と同じ形式で実施されます。途中で中断することはできません。
                全4タスクを連続で実施し、最後に総合採点を行います。
              </p>
            </div>

            <button
              onClick={() => startTask(1, examState.problems[0])}
              className="btn-primary text-lg px-8 py-4"
            >
              模擬試験を開始する
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}