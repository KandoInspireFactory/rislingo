/**
 * PracticeLayout - Common layout for practice phases
 * 
 * Provides consistent header, progress bar, and main content wrapper
 * for all practice phase pages (Reading, Listening, Preparation, Speaking)
 */

'use client';

import { useRouter } from 'next/navigation';

interface PracticeLayoutProps {
  children: React.ReactNode;
  phase: 'Reading' | 'Listening' | 'Preparation' | 'Speaking';
  phaseNumber: 1 | 2 | 3 | 4;
  taskType?: string;
  isMockExam?: boolean;
}

export default function PracticeLayout({ 
  children, 
  phase, 
  phaseNumber,
  taskType = 'task3',
  isMockExam = false
}: PracticeLayoutProps) {
  const router = useRouter();

  const handleBackToHome = () => {
    router.push('/home');
  };

  const progressPercentage = (phaseNumber / 4) * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header - Responsive */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <h1 className="text-lg sm:text-xl md:text-2xl font-bold text-gray-900">
                {taskType.toUpperCase()} - {phase} Phase
              </h1>
              {isMockExam && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  模擬試験
                </span>
              )}
            </div>
            <button
              onClick={handleBackToHome}
              className="text-xs sm:text-sm text-gray-600 hover:text-gray-900 transition-colors px-2 sm:px-3 py-1 sm:py-2 rounded hover:bg-gray-100"
            >
              中止
            </button>
          </div>
        </div>
      </header>

      {/* Progress Bar - Responsive */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs sm:text-sm font-medium text-indigo-600">{taskType.toUpperCase()} - {phase}</span>
            <span className="text-xs sm:text-sm text-gray-500">{phaseNumber} / 4</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5 sm:h-2">
            <div 
              className="bg-indigo-600 h-1.5 sm:h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Content - Responsive */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {children}
      </main>
    </div>
  );
}
