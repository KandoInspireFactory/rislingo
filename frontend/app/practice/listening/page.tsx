/**
 * Listening Phase - Task 3 Practice Flow
 * 
 * Features:
 * - Audio playback with progress bar
 * - Waveform visualizer
 * - Optional real-time subtitles
 * - Auto-transition to Preparation Phase when audio completes
 * 
 * Requirements: 3.2
 */

'use client';

import { useEffect, useState, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import LoadingSpinner from '@/components/LoadingSpinner';
import { Problem } from '@/lib/types';

function ListeningPhaseContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const audioRef = useRef<HTMLAudioElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | undefined>(undefined);
  
  const [problem, setProblem] = useState<Problem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showSubtitles, setShowSubtitles] = useState(false);
  
  // Get selected task type from URL params
  const selectedTask = searchParams.get('task') || 'task3';

  // Get full audio URL
  const getAudioUrl = (relativeUrl: string): string => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return `${apiBaseUrl}${relativeUrl}`;
  };

  // Load problem data
  useEffect(() => {
    const problemData = searchParams.get('problem');
    console.log('🔍 Problem data from URL:', problemData ? 'found' : 'not found');
    
    if (problemData) {
      console.log('📝 Attempting to parse problem data from URL...');
      const decodedData = decodeURIComponent(problemData);
      const parsedProblem = safeParseProblemData(decodedData, 'URL');
      
      if (parsedProblem) {
        setProblem(parsedProblem);
        setIsLoading(false);
        console.log('✅ Successfully loaded problem from URL:', parsedProblem.problem_id);
      } else {
        console.log('🔄 Invalid URL data, falling back to sessionStorage...');
        tryLoadFromSessionStorage();
      }
    } else {
      console.log('🔄 No URL parameter, trying sessionStorage...');
      // Try to get from sessionStorage
      tryLoadFromSessionStorage();
    }
  }, [searchParams]);

  const safeParseProblemData = (data: string, source: string) => {
    try {
      if (!data || data === 'undefined' || data === 'null') {
        console.warn(`⚠️ Invalid problem data from ${source}:`, data);
        return null;
      }
      
      const parsed = JSON.parse(data);
      if (!parsed || !parsed.problem_id) {
        console.warn(`⚠️ Problem data missing required fields from ${source}:`, parsed);
        return null;
      }
      
      return parsed;
    } catch (err) {
      console.error(`❌ Failed to parse problem data from ${source}:`, err);
      return null;
    }
  };

  const tryLoadFromSessionStorage = () => {
    const storedProblem = sessionStorage.getItem('currentProblem');
    console.log('🔍 Checking sessionStorage for problem data:', storedProblem ? 'found' : 'not found');
    
    const parsedProblem = safeParseProblemData(storedProblem || '', 'sessionStorage');
    
    if (parsedProblem) {
      setProblem(parsedProblem);
      setIsLoading(false);
      console.log('📖 Loaded problem from sessionStorage:', parsedProblem.problem_id);
    } else {
      console.warn('⚠️ No valid problem data found in sessionStorage');
      setError('問題データが見つかりません。');
      setIsLoading(false);
    }
  };

  // Initialize audio and start playback
  useEffect(() => {
    if (problem && audioRef.current) {
      const audio = audioRef.current;
      
      // Set up event listeners
      const handleLoadedMetadata = () => {
        setDuration(audio.duration);
      };
      
      const handleTimeUpdate = () => {
        setCurrentTime(audio.currentTime);
      };
      
      const handlePlay = () => {
        setIsPlaying(true);
      };
      
      const handlePause = () => {
        setIsPlaying(false);
      };
      
      const handleEnded = () => {
        setIsPlaying(false);
        // Auto-transition to Preparation Phase
        if (problem) {
          // Check if this is a mock exam
          const isMockExam = searchParams.get('mockExam') === 'true';
          const mockExamParam = isMockExam ? '&mockExam=true' : '';
          
          const problemParam = encodeURIComponent(JSON.stringify(problem));
          router.push(`/practice/preparation?problem=${problemParam}&task=${selectedTask}${mockExamParam}`);
        }
      };
      
      const handleError = (e: Event) => {
        console.error('Audio playback error:', e);
        setError('音声の再生に失敗しました。');
      };
      
      audio.addEventListener('loadedmetadata', handleLoadedMetadata);
      audio.addEventListener('timeupdate', handleTimeUpdate);
      audio.addEventListener('play', handlePlay);
      audio.addEventListener('pause', handlePause);
      audio.addEventListener('ended', handleEnded);
      audio.addEventListener('error', handleError);
      
      // Auto-play audio
      audio.play().catch((err) => {
        console.error('Auto-play failed:', err);
        setError('音声の自動再生に失敗しました。再生ボタンをクリックしてください。');
      });
      
      return () => {
        audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
        audio.removeEventListener('timeupdate', handleTimeUpdate);
        audio.removeEventListener('play', handlePlay);
        audio.removeEventListener('pause', handlePause);
        audio.removeEventListener('ended', handleEnded);
        audio.removeEventListener('error', handleError);
      };
    }
  }, [problem, router]);

  // Waveform visualizer
  useEffect(() => {
    if (!canvasRef.current || !isPlaying) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      const width = canvas.width;
      const height = canvas.height;
      
      // Clear canvas
      ctx.clearRect(0, 0, width, height);
      
      // Draw animated waveform
      ctx.strokeStyle = '#4F46E5'; // indigo-600
      ctx.lineWidth = 2;
      ctx.beginPath();
      
      const time = Date.now() / 1000;
      const amplitude = height / 4;
      const frequency = 2;
      const speed = 2;
      
      for (let x = 0; x < width; x++) {
        const y = height / 2 + 
          Math.sin((x / width) * frequency * Math.PI * 2 + time * speed) * amplitude * 
          (0.5 + Math.random() * 0.5);
        
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      
      ctx.stroke();
      
      animationFrameRef.current = requestAnimationFrame(draw);
    };
    
    draw();
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isPlaying]);

  const handleBackToHome = () => {
    // Pause audio before leaving
    if (audioRef.current) {
      audioRef.current.pause();
    }
    router.push('/home');
  };

  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !problem) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto px-4 text-center">
          <div className="bg-white rounded-xl shadow-md p-8">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">エラー</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={handleBackToHome}
              className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
            >
              ホームに戻る
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 fade-enter">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                {selectedTask.toUpperCase()} - Listening Phase
              </h1>
              {searchParams.get('mockExam') === 'true' && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  模擬試験
                </span>
              )}
            </div>
            <button
              onClick={handleBackToHome}
              className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              中止
            </button>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-indigo-600">Listening</span>
            <span className="text-sm text-gray-500">2 / 4</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: '50%' }}
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Audio Player Section */}
        <div className="bg-white rounded-xl shadow-md p-6 sm:p-8 mb-6">
          <div className="text-center mb-6">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">
              {selectedTask === 'task2' ? 'Student Conversation' : 'Lecture Audio'}
            </h2>
            <p className="text-sm text-gray-600">
              講義音声を聴いてください。
            </p>
          </div>

          {/* Waveform Visualizer */}
          <div className="mb-6 bg-gray-50 rounded-lg p-4">
            <canvas
              ref={canvasRef}
              width={600}
              height={100}
              className="w-full h-24"
              style={{ maxWidth: '100%' }}
            />
          </div>

          {/* Audio Controls */}
          <div className="space-y-4">
            {/* Progress Bar */}
            <div className="relative">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-indigo-600 h-2 rounded-full transition-all duration-100"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
              <div className="flex justify-between mt-2 text-xs text-gray-600">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>

            {/* Play/Pause Button */}
            <div className="flex justify-center">
              <button
                onClick={togglePlayPause}
                className="w-16 h-16 bg-indigo-600 hover:bg-indigo-700 rounded-full flex items-center justify-center transition-colors shadow-lg"
                aria-label={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? (
                  <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                  </svg>
                ) : (
                  <svg className="w-8 h-8 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                )}
              </button>
            </div>

            {/* Subtitle Toggle */}
            <div className="flex justify-center">
              <button
                onClick={() => setShowSubtitles(!showSubtitles)}
                className="text-sm text-indigo-600 hover:text-indigo-700 transition-colors"
              >
                {showSubtitles ? '字幕を非表示' : '字幕を表示（オプション）'}
              </button>
            </div>
          </div>

          {/* Hidden Audio Element */}
          <audio
            ref={audioRef}
            src={getAudioUrl(problem.lecture_audio_url)}
            preload="auto"
          />
        </div>

        {/* Subtitles Section (Optional) */}
        {showSubtitles && (
          <div className="bg-white rounded-xl shadow-md p-6 sm:p-8 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              字幕（参考）
            </h3>
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {problem.lecture_script}
              </p>
            </div>
          </div>
        )}

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
                音声が終了すると、自動的に次のフェーズ（Preparation）に進みます。
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function ListeningPhasePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    }>
      <ListeningPhaseContent />
    </Suspense>
  );
}
