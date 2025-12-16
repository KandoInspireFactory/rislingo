/**
 * Speaking Phase - Task 3 Practice Flow
 * 
 * Features:
 * - 60-second countdown timer
 * - Automatic recording start
 * - Recording indicator and waveform display
 * - Auto-stop recording after 60 seconds and transition to results screen
 * 
 * Requirements: 3.4, 3.6
 */

'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Timer from '@/components/Timer';
import AudioRecorder from '@/components/AudioRecorder';
import LoadingSpinner from '@/components/LoadingSpinner';
import PracticeLayout from '@/components/PracticeLayout';
import ErrorScreen from '@/components/ErrorScreen';
import { useProblemData } from '@/hooks/useProblemData';

function SpeakingPhaseContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { problem, isLoading, error } = useProblemData();
  const [recordingComplete, setRecordingComplete] = useState(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [processingStage, setProcessingStage] = useState<'transcribing' | 'scoring' | null>(null);
  
  // Get selected task type from URL params
  const selectedTask = searchParams.get('task') || 'task3';
  
  // Set speaking time based on task type
  const speakingTime = selectedTask === 'task1' ? 45 : 60;

  // Handle timer completion - recording will auto-stop via AudioRecorder
  const handleTimerComplete = () => {
    console.log(`⏰ Timer completed - ${speakingTime} seconds elapsed`);
    // Timer completion triggers auto-stop in AudioRecorder
    // We'll transition to results after recording completes
  };

  // Handle recording completion
  const handleRecordingComplete = async (blob: Blob) => {
    console.log('🎤 Recording complete. Blob size:', blob.size, 'bytes');
    
    // Prevent duplicate processing
    if (recordingComplete) {
      console.warn('⚠️ Recording already being processed, ignoring duplicate call');
      return;
    }
    
    setRecordingComplete(true);
    
    if (!problem) {
      setRecordingError('問題データが見つかりません。');
      return;
    }

    // Timeout for the entire processing (90 seconds total)
    const TOTAL_TIMEOUT = 90000; // 90 seconds
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error('処理がタイムアウトしました（90秒）')), TOTAL_TIMEOUT);
    });

    try {
      // Import API functions dynamically to avoid circular dependencies
      const { transcribeAudio, evaluateResponse, evaluateTask1Response } = await import('@/lib/api-client');
      
      // Wrap the entire process in a race with timeout
      await Promise.race([
        (async () => {
          // Step 1: Transcribe audio
          console.log('📝 Starting transcription...');
          setProcessingStage('transcribing');
          const transcriptionStart = Date.now();
          const transcriptionResult = await transcribeAudio(blob, problem.problem_id);
          const transcript = transcriptionResult.transcript;
          console.log('✅ Transcription complete in', (Date.now() - transcriptionStart) / 1000, 'seconds');
          console.log('📄 Transcript:', transcript.substring(0, 100) + '...');

          // Step 2: Evaluate response based on task type
          console.log('🤖 Starting AI scoring...');
          setProcessingStage('scoring');
          const scoringStart = Date.now();
          
          let scoringResult;
          if (selectedTask === 'task1') {
            scoringResult = await evaluateTask1Response({
              problem_id: problem.problem_id,
              transcript: transcript,
              question: problem.question,
            });
          } else {
            scoringResult = await evaluateResponse({
              problem_id: problem.problem_id,
              transcript: transcript,
              reading_text: problem.reading_text ?? '',
              lecture_script: problem.lecture_script ?? '',
            });
          }
          
          console.log('✅ Scoring complete in', (Date.now() - scoringStart) / 1000, 'seconds');
          console.log('📊 Score:', scoringResult.overall_score);

          // Check if this is a mock exam
          const isMockExam = sessionStorage.getItem('isMockExam') === 'true';
          
          if (isMockExam) {
            // Handle mock exam flow
            console.log('🎯 Mock exam mode: processing task completion...');
            await handleMockExamTaskCompletion(transcript, scoringResult);
          } else {
            // Regular practice mode
            sessionStorage.setItem('scoringResult', JSON.stringify(scoringResult));
            sessionStorage.setItem('currentProblem', JSON.stringify(problem));
            console.log('🎯 Navigating to results page...');
            router.push(`/practice/results?task=${selectedTask}`);
          }
        })(),
        timeoutPromise
      ]);
    } catch (error) {
      console.error('❌ Error processing recording:', error);
      
      // Detailed error message for debugging
      let errorMessage = '録音の処理中にエラーが発生しました。';
      
      if (error instanceof Error) {
        console.error('Error details:', {
          message: error.message,
          name: error.name,
          stack: error.stack
        });
        
        if (error.message.includes('401') || error.message.includes('API key')) {
          errorMessage = 'API認証エラーです。OpenAI APIキーを確認してください。';
        } else if (error.message.includes('timeout') || error.message.includes('タイムアウト')) {
          errorMessage = '処理がタイムアウトしました。もう一度お試しください。';
        } else if (error.message.includes('network') || error.message.includes('Failed to fetch')) {
          errorMessage = 'ネットワークエラーです。インターネット接続を確認してください。';
        } else {
          errorMessage = `エラー: ${error.message}`;
        }
      }
      
      setRecordingError(errorMessage);
      setRecordingComplete(false);
      setProcessingStage(null);
    }
  };

  // Handle mock exam task completion
  const handleMockExamTaskCompletion = async (transcript: string, scoringResult: any) => {
    try {
      // Get current mock exam state
      const mockExamStateStr = sessionStorage.getItem('mockExamState');
      if (!mockExamStateStr) {
        throw new Error('Mock exam state not found');
      }

      const mockExamState = JSON.parse(mockExamStateStr);
      const currentTaskIndex = mockExamState.currentTask - 1;

      // Store transcript and scoring result
      mockExamState.transcripts[currentTaskIndex] = transcript;
      
      console.log(`✅ Task ${mockExamState.currentTask} completed with score: ${scoringResult.overall_score}`);

      // Check if this was the last task
      if (mockExamState.currentTask >= 4) {
        // All tasks completed - go to results
        console.log('🎉 All mock exam tasks completed!');
        
        // Store final results
        sessionStorage.setItem('mockExamResults', JSON.stringify({
          problems: mockExamState.problems,
          transcripts: mockExamState.transcripts
        }));
        
        router.push('/practice/mock-exam/results');
      } else {
        // Move to next task
        const nextTask = mockExamState.currentTask + 1;
        mockExamState.currentTask = nextTask;
        
        // Update state
        sessionStorage.setItem('mockExamState', JSON.stringify(mockExamState));
        
        console.log(`🚀 Moving to Task ${nextTask}`);
        
        // Navigate to next task
        const nextProblem = mockExamState.problems[nextTask - 1];
        sessionStorage.setItem('currentProblem', JSON.stringify(nextProblem));
        
        if (nextTask === 1) {
          router.push(`/practice/preparation?task=task1&mockExam=true`);
        } else if (nextTask === 4) {
          const problemParam = encodeURIComponent(JSON.stringify(nextProblem));
          router.push(`/practice/listening?problem=${problemParam}&task=task4&mockExam=true`);
        } else {
          router.push(`/practice/reading?task=task${nextTask}&mockExam=true`);
        }
      }
    } catch (error) {
      console.error('❌ Error handling mock exam task completion:', error);
      alert('模擬試験の進行中にエラーが発生しました。');
      router.push('/practice/select');
    }
  };

  // Handle recording error
  const handleRecordingError = (err: Error) => {
    setRecordingError(err.message);
  };

  // Show loading screen
  if (isLoading) {
    return <ErrorScreen error="" showLoading />;
  }

  // Show error screen
  if (error || !problem) {
    return <ErrorScreen error={error || '不明なエラーが発生しました。'} />;
  }

  // Show recording error with retry option
  if (recordingError) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--background)' }}>
        <div className="max-w-md mx-auto px-4 text-center">
          <div className="luxury-card rounded-2xl p-10">
            <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6" style={{
              background: 'rgba(220, 38, 38, 0.1)',
              border: '1px solid rgba(220, 38, 38, 0.3)'
            }}>
              <svg className="w-10 h-10" style={{ color: '#fca5a5' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold mb-3" style={{ color: 'var(--foreground)' }}>エラーが発生しました</h2>
            <p className="mb-8 font-light" style={{ color: 'var(--foreground-muted)' }}>{recordingError}</p>
            <div className="space-y-4">
              <button
                onClick={() => {
                  setRecordingError(null);
                  router.push('/practice/reading');
                }}
                className="btn-luxury w-full py-4 px-6 rounded-xl font-semibold tracking-wide"
              >
                もう一度練習する
              </button>
              <button
                onClick={() => router.push('/home')}
                className="w-full py-4 px-6 rounded-xl font-semibold tracking-wide transition-all duration-300"
                style={{
                  background: 'var(--background-elevated)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--foreground-muted)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-color-gold)';
                  e.currentTarget.style.color = 'var(--color-accent-gold)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-color)';
                  e.currentTarget.style.color = 'var(--foreground-muted)';
                }}
              >
                ホームに戻る
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (recordingComplete) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--background)' }}>
        <div className="max-w-md mx-auto px-4 text-center">
          <div className="luxury-card rounded-2xl p-10">
            <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-8" style={{
              background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%)',
              border: '1px solid var(--border-color-gold)'
            }}>
              <svg className="w-10 h-10 gold-accent animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            
            <h2 className="text-2xl font-bold mb-6 gold-accent">採点中</h2>
            
            {/* Progress steps */}
            <div className="space-y-4 mb-8">
              <div className={`flex items-center justify-center space-x-3 ${processingStage === 'transcribing' ? 'gold-accent' : processingStage === 'scoring' ? '' : ''}`} style={{
                color: processingStage === 'transcribing' ? 'var(--color-accent-gold)' : processingStage === 'scoring' ? '#059669' : 'var(--foreground-muted)'
              }}>
                {processingStage === 'scoring' ? (
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20" style={{ color: '#059669' }}>
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                ) : processingStage === 'transcribing' ? (
                  <svg className="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <div className="w-6 h-6 border-2 rounded-full" style={{ borderColor: 'var(--border-color)' }}></div>
                )}
                <span className="text-sm font-light tracking-wide">音声を文字起こし中</span>
              </div>
              
              <div className={`flex items-center justify-center space-x-3`} style={{
                color: processingStage === 'scoring' ? 'var(--color-accent-gold)' : 'var(--foreground-muted)'
              }}>
                {processingStage === 'scoring' ? (
                  <svg className="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <div className="w-6 h-6 border-2 rounded-full" style={{ borderColor: 'var(--border-color)' }}></div>
                )}
                <span className="text-sm font-light tracking-wide">AIが採点中</span>
              </div>
            </div>
            
            <p className="text-sm font-light" style={{ color: 'var(--foreground-muted)' }}>
              {processingStage === 'transcribing' && '音声を文字起こししています（5-15秒）'}
              {processingStage === 'scoring' && 'AIが採点しています（10-20秒）'}
            </p>
            <p className="text-xs font-light mt-2" style={{ color: 'var(--foreground-muted)' }}>
              少々お待ちください
            </p>
          </div>
        </div>
      </div>
    );
  }

  const isMockExam = searchParams.get('mockExam') === 'true';

  return (
    <PracticeLayout phase="Speaking" phaseNumber={4} taskType={selectedTask} isMockExam={isMockExam}>
      <div className="fade-enter">
        {/* Timer Section */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-4">回答時間</p>
            <Timer 
              duration={speakingTime} 
              onComplete={handleTimerComplete}
              warningThreshold={15}
            />
          </div>
        </div>

        {/* Question Display */}
        <div className="bg-white rounded-xl shadow-md p-6 sm:p-8 mb-6">
          <div className="mb-4">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">
              Question
            </h2>
          </div>
          
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 sm:p-6">
            <p className="text-gray-800 leading-relaxed">
              {problem.question}
            </p>
          </div>
        </div>

        {/* Recording Section */}
        <div className="bg-white rounded-xl shadow-md p-6 sm:p-8 mb-6">
          <div className="mb-6">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">
              録音
            </h2>
            <p className="text-sm text-gray-600">
              マイクに向かって回答してください。録音は自動的に開始されます。
            </p>
          </div>
          
          <AudioRecorder
            duration={speakingTime}
            onRecordingComplete={handleRecordingComplete}
            onError={handleRecordingError}
            autoStart={true}
          />
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
                60秒経過すると、録音は自動的に停止し、採点結果画面に移動します。
              </p>
            </div>
          </div>
        </div>
      </div>
      </PracticeLayout>
  );
}

export default function SpeakingPhasePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    }>
      <SpeakingPhaseContent />
    </Suspense>
  );
}
