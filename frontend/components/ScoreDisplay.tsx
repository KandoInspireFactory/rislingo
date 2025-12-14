/**
 * ScoreDisplay component - Displays TOEFL Speaking scoring results
 * 
 * Features:
 * - Overall score and detailed scores for 3 criteria
 * - Feedback and improvement advice for each criterion
 * - Model answer tab with highlighted phrases
 * - Disclaimer about AI scoring
 * - "Practice Again" and "Return to Home" buttons
 * 
 * Requirements: 5.2, 5.4, 6.1, 6.2, 6.3, 6.4
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ScoringResponse, ModelAnswerResponse, Problem } from '@/lib/types';
import { generateModelAnswer, savePhrase } from '@/lib/api-client';
import LoadingSpinner from './LoadingSpinner';

interface ScoreDisplayProps {
  scoringResult: ScoringResponse | any; // Task1の場合は異なる形式
  taskType?: string;
  isMockExam?: boolean; // 模擬試験かどうかのフラグ
}

export default function ScoreDisplay({ scoringResult, taskType = 'task3', isMockExam = false }: ScoreDisplayProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'scores' | 'model'>('scores');
  const [previousTab, setPreviousTab] = useState<'scores' | 'model'>('scores');
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [modelAnswer, setModelAnswer] = useState<ModelAnswerResponse | null>(null);
  const [isLoadingModel, setIsLoadingModel] = useState(false);
  const [modelError, setModelError] = useState<string | null>(null);
  const [savingPhraseId, setSavingPhraseId] = useState<number | null>(null);
  const [savedPhrases, setSavedPhrases] = useState<Set<number>>(new Set());
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [customPhrase, setCustomPhrase] = useState('');
  const [isSavingCustom, setIsSavingCustom] = useState(false);
  const [hasLoadedModel, setHasLoadedModel] = useState(false); // 重複生成防止フラグ
  
  // AI添削機能の状態
  const [showAIReview, setShowAIReview] = useState(false);
  const [aiReview, setAiReview] = useState<any>(null);
  const [isLoadingAIReview, setIsLoadingAIReview] = useState(false);
  const [aiReviewError, setAiReviewError] = useState<string | null>(null);
  
  // 音声再生機能の状態
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  // Check if this is Task 1
  const isTask1 = taskType === 'task1';

  // Handle tab change with animation
  const handleTabChange = (newTab: 'scores' | 'model') => {
    if (newTab === activeTab) return;
    
    console.log(`🔄 Switching to ${newTab} tab`);
    
    // 模範解答タブに切り替える時は、既に生成済みの場合は何もしない
    if (newTab === 'model' && modelAnswer) {
      console.log('✅ Model answer already exists, no need to regenerate');
    }
    
    setIsTransitioning(true);
    setPreviousTab(activeTab);
    
    // Small delay to allow exit animation
    setTimeout(() => {
      setActiveTab(newTab);
      setIsTransitioning(false);
    }, 200); // Match slide animation duration
  };

  // Score color based on value (0-4 scale)
  const getScoreColor = (score: number): string => {
    if (score >= 3.5) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 2.5) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (score >= 1.5) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  // Score label based on official TOEFL criteria
  const getScoreLabel = (score: number): string => {
    if (score === 4) return '英語の表現がよく、構成も回答もよい';
    if (score === 3) return 'テンポと構成よく問に答えきれている';
    if (score === 2) return 'テンポと構成がまずく問に答えきれていない';
    if (score === 1) return 'ほとんど話していない';
    return '全く話していない';
  };

  // Category label in Japanese
  const getCategoryLabel = (category: string): string => {
    if (isTask1) {
      switch (category) {
        case 'introduction': return '導入表現';
        case 'transition': return '接続表現';
        case 'example': return '例示表現';
        case 'conclusion': return '結論表現';
        default: return category;
      }
    } else {
      switch (category) {
        case 'transition': return '接続表現';
        case 'example': return '例示表現';
        case 'conclusion': return '結論表現';
        default: return category;
      }
    }
  };

  // Category color
  const getCategoryColor = (category: string): string => {
    switch (category) {
      case 'introduction': return 'bg-indigo-100 text-indigo-800 border-indigo-300';
      case 'transition': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'example': return 'bg-green-100 text-green-800 border-green-300';
      case 'conclusion': return 'bg-purple-100 text-purple-800 border-purple-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  // Load model answer immediately when component mounts (background loading)
  useEffect(() => {
    // 重複生成を防ぐ：まだ生成していない、かつ生成中でない場合のみ
    if (!hasLoadedModel && !isLoadingModel && !modelAnswer) {
      console.log('🚀 Starting background model answer generation...');
      loadModelAnswer();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 空の依存配列でマウント時のみ実行

  const loadModelAnswer = async () => {
    // 重複生成を防ぐ：既に生成済み、生成中、または結果が存在する場合はスキップ
    if (hasLoadedModel || isLoadingModel || modelAnswer) {
      console.log('⏭️ Model answer already loaded or loading, skipping...');
      return;
    }

    setIsLoadingModel(true);
    setHasLoadedModel(true); // フラグを立てて重複生成を防ぐ
    setModelError(null);

    try {
      // Get problem data from session storage
      const problemData = sessionStorage.getItem('currentProblem');
      if (!problemData) {
        console.error('❌ No problem data found in session storage');
        throw new Error('問題データが見つかりません。ページをリロードせずに練習を完了してください。');
      }

      console.log('📖 Problem data loaded from session storage');
      const problem: Problem = JSON.parse(problemData);

      // Generate model answer based on task type
      console.log('🤖 Generating model answer...');
      const startTime = Date.now();
      let result;
      
      if (isTask1) {
        const { generateTask1ModelAnswer } = await import('@/lib/api-client');
        result = await generateTask1ModelAnswer({
          problem_id: problem.problem_id,
          question: problem.question
        });
      } else if (taskType === 'task2') {
        const { generateTask2ModelAnswer } = await import('@/lib/api-client');
        result = await generateTask2ModelAnswer({
          problem_id: problem.problem_id,
          announcement_text: problem.reading_text || '',
          conversation_script: problem.lecture_script || '',
          question: problem.question
        });
      } else {
        result = await generateModelAnswer({
          problem_id: problem.problem_id,
          reading_text: problem.reading_text || '',
          lecture_script: problem.lecture_script || '',
          question: problem.question
        });
      }

      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log(`✅ Model answer generated successfully in ${duration}s`);
      setModelAnswer(result);
    } catch (error) {
      console.error('❌ Model answer generation error:', error);
      setModelError(error instanceof Error ? error.message : '模範解答の生成に失敗しました。');
      setHasLoadedModel(false); // エラー時はフラグをリセットして再試行可能にする
    } finally {
      setIsLoadingModel(false);
    }
  };

  const handlePracticeAgain = () => {
    try {
      // Get current problem data to determine task type and navigation
      const problemData = sessionStorage.getItem('currentProblem');
      
      if (!problemData) {
        // If no problem data, go to home
        router.push('/home');
        return;
      }

      const problem = JSON.parse(problemData);
      const currentTaskType = taskType || 'task3';
      
      // Clear only the scoring result, keep the problem data for reuse
      sessionStorage.removeItem('scoringResult');
      
      // Navigate to the appropriate phase based on task type
      if (currentTaskType === 'task1') {
        // Task1: Go directly to preparation phase
        router.push(`/practice/preparation?task=${currentTaskType}`);
      } else if (currentTaskType === 'task4') {
        // Task4: Go directly to listening phase (no reading)
        const problemParam = encodeURIComponent(JSON.stringify(problem));
        router.push(`/practice/listening?problem=${problemParam}&task=${currentTaskType}`);
      } else {
        // Task2, Task3: Start from reading phase
        router.push(`/practice/reading?task=${currentTaskType}`);
      }
      
      console.log(`🔄 Restarting ${currentTaskType} practice with same problem`);
      
    } catch (error) {
      console.error('Error restarting practice:', error);
      // Fallback to home if there's an error
      sessionStorage.removeItem('currentProblem');
      sessionStorage.removeItem('scoringResult');
      router.push('/home');
    }
  };

  const handleReturnHome = () => {
    // Clear session storage when returning home
    sessionStorage.removeItem('currentProblem');
    sessionStorage.removeItem('scoringResult');
    router.push('/home');
  };

  const handleSavePhrase = async (phrase: ModelAnswerResponse['highlighted_phrases'][0], index: number) => {
    setSavingPhraseId(index);
    setSaveMessage(null);

    try {
      // Get user identifier from localStorage (not UUID, but the login identifier)
      const userIdentifier = localStorage.getItem('user_identifier');
      
      if (!userIdentifier) {
        console.error('❌ No user_identifier found in localStorage');
        console.error('Available localStorage keys:', Object.keys(localStorage));
        console.error('localStorage contents:', {
          user_id: localStorage.getItem('user_id'),
          userId: localStorage.getItem('userId'),
          session_token: localStorage.getItem('session_token'),
          user_identifier: localStorage.getItem('user_identifier')
        });
        throw new Error('ログインが必要です。ホームに戻ってログインしてください。');
      }

      console.log('💾 Saving phrase for user:', userIdentifier);

      // Save phrase (use user_identifier, not UUID)
      await savePhrase(
        userIdentifier,
        phrase.text,
        modelAnswer?.model_answer || '',
        phrase.category
      );

      // Mark as saved
      setSavedPhrases(prev => new Set(prev).add(index));
      setSaveMessage('フレーズが保存されました');

      // Clear message after 3 seconds
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      console.error('Phrase save error:', error);
      setSaveMessage(error instanceof Error ? error.message : 'フレーズの保存に失敗しました。');
    } finally {
      setSavingPhraseId(null);
    }
  };

  const handleSaveCustomPhrase = async () => {
    if (!customPhrase.trim()) {
      setSaveMessage('フレーズを入力してください');
      setTimeout(() => setSaveMessage(null), 3000);
      return;
    }

    setIsSavingCustom(true);
    setSaveMessage(null);

    try {
      // Get user identifier from localStorage (not UUID, but the login identifier)
      const userIdentifier = localStorage.getItem('user_identifier');
      
      if (!userIdentifier) {
        console.error('❌ No user_identifier found in localStorage');
        console.error('Available localStorage keys:', Object.keys(localStorage));
        console.error('localStorage contents:', {
          user_id: localStorage.getItem('user_id'),
          userId: localStorage.getItem('userId'),
          session_token: localStorage.getItem('session_token'),
          user_identifier: localStorage.getItem('user_identifier')
        });
        throw new Error('ログインが必要です。ホームに戻ってログインしてください。');
      }

      console.log('💾 Saving custom phrase for user:', userIdentifier);

      // Save custom phrase (use user_identifier, not UUID)
      await savePhrase(
        userIdentifier,
        customPhrase.trim(),
        modelAnswer?.model_answer || '',
        'custom'
      );

      setSaveMessage('カスタムフレーズが保存されました');
      setCustomPhrase(''); // Clear input

      // Clear message after 3 seconds
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      console.error('Custom phrase save error:', error);
      setSaveMessage(error instanceof Error ? error.message : 'フレーズの保存に失敗しました。');
    } finally {
      setIsSavingCustom(false);
    }
  };

  // AI添削機能
  const handleAIReview = async () => {
    if (showAIReview && aiReview) {
      // 既に表示されている場合は閉じる
      setShowAIReview(false);
      return;
    }

    if (aiReview) {
      // 既に生成済みの場合は表示するだけ
      setShowAIReview(true);
      return;
    }

    setIsLoadingAIReview(true);
    setAiReviewError(null);

    try {
      // Get problem data from session storage
      const problemData = sessionStorage.getItem('currentProblem');
      console.log('📦 Raw problem data from session:', problemData);
      
      if (!problemData) {
        throw new Error('問題データが見つかりません。');
      }

      const problem = JSON.parse(problemData);
      console.log('📋 Parsed problem data:', problem);
      console.log('📝 Scoring result:', scoringResult);
      console.log('🏷️ Task type:', taskType);
      
      // Validate required data
      if (!problem.problem_id) {
        throw new Error('問題IDが見つかりません。');
      }
      
      if (!scoringResult.user_transcript) {
        throw new Error('ユーザーの回答が見つかりません。');
      }
      
      if (!problem.question) {
        throw new Error('問題の質問が見つかりません。');
      }
      
      // Import API function dynamically
      const { generateAIReview } = await import('@/lib/api-client');

      console.log('🤖 Generating AI review...');
      
      const startTime = Date.now();
      
      // Generate AI review based on task type
      let result;
      if (isTask1) {
        const payload = {
          task_type: 'task1',
          problem_id: problem.problem_id,
          user_transcript: scoringResult.user_transcript,
          question: problem.question
        };
        console.log('📤 Task1 AI review payload:', payload);
        result = await generateAIReview(payload);
      } else if (taskType === 'task2') {
        const payload = {
          task_type: 'task2',
          problem_id: problem.problem_id,
          user_transcript: scoringResult.user_transcript,
          announcement_text: problem.reading_text || '',
          conversation_script: problem.lecture_script || '',
          question: problem.question
        };
        console.log('📤 Task2 AI review payload:', payload);
        result = await generateAIReview(payload);
      } else if (taskType === 'task4') {
        const payload = {
          task_type: 'task4',
          problem_id: problem.problem_id,
          user_transcript: scoringResult.user_transcript,
          lecture_script: problem.lecture_script || '',
          question: problem.question
        };
        console.log('📤 Task4 AI review payload:', payload);
        result = await generateAIReview(payload);
      } else {
        // Task 3
        const payload = {
          task_type: 'task3',
          problem_id: problem.problem_id,
          user_transcript: scoringResult.user_transcript,
          reading_text: problem.reading_text || '',
          lecture_script: problem.lecture_script || '',
          question: problem.question
        };
        console.log('📤 Task3 AI review payload:', payload);
        result = await generateAIReview(payload);
      }

      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log(`✅ AI review generated successfully in ${duration}s`);
      
      setAiReview(result);
      setShowAIReview(true);
    } catch (error) {
      console.error('❌ AI review generation error:', error);
      setAiReviewError(error instanceof Error ? error.message : 'AI添削の生成に失敗しました。');
    } finally {
      setIsLoadingAIReview(false);
    }
  };

  // 音声生成と再生機能
  const handleGenerateAndPlayAudio = async (text: string) => {
    if (!text || !text.trim()) {
      alert('音声生成するテキストがありません。');
      return;
    }

    // Stop any currently playing audio and wait a bit
    handleStopAudio();
    await new Promise(resolve => setTimeout(resolve, 100));

    setIsGeneratingAudio(true);

    try {
      // Import API function dynamically
      const { generateSpeechAudio } = await import('@/lib/api-client');

      console.log('🔊 Generating speech audio...');
      const audioBlob = await generateSpeechAudio(text);

      // Clean up previous audio URL if exists
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }

      // Create new audio URL
      const url = URL.createObjectURL(audioBlob);
      setAudioUrl(url);

      // Create and configure audio element
      const audio = new Audio(url);
      
      // Preload the audio
      audio.preload = 'auto';
      audio.load();

      // Set up event listeners before assigning to ref
      audio.onplay = () => {
        console.log('🎵 Audio started playing');
        setIsPlaying(true);
      };
      
      audio.onpause = () => {
        console.log('⏸️ Audio paused');
        setIsPlaying(false);
      };
      
      audio.onended = () => {
        console.log('🏁 Audio playback ended');
        setIsPlaying(false);
      };
      
      audio.onerror = (e) => {
        console.error('❌ Audio playback error:', e);
        setIsPlaying(false);
        alert('音声の再生に失敗しました。');
      };

      // Wait for audio to be ready
      await new Promise((resolve, reject) => {
        audio.oncanplaythrough = resolve;
        audio.onerror = reject;
        // Timeout after 5 seconds
        setTimeout(() => reject(new Error('Audio loading timeout')), 5000);
      });

      // Assign to ref after setup
      audioRef.current = audio;

      // Start playback with better error handling
      try {
        const playPromise = audio.play();
        
        if (playPromise !== undefined) {
          await playPromise;
          console.log('✅ Audio playback started successfully');
        }
      } catch (playError: any) {
        console.error('❌ Audio play() failed:', playError);
        setIsPlaying(false);
        
        // Handle specific error types
        if (playError.name === 'AbortError') {
          console.log('ℹ️ Audio play was interrupted, this is normal');
          return; // Don't show error for AbortError
        } else if (playError.name === 'NotAllowedError') {
          alert('ブラウザの自動再生がブロックされています。ページをクリックしてから再度お試しください。');
        } else if (playError.name === 'NotSupportedError') {
          alert('この音声形式はサポートされていません。');
        } else {
          alert('音声の再生に失敗しました。もう一度お試しください。');
        }
        return;
      }

    } catch (error) {
      console.error('❌ Audio generation/playback error:', error);
      
      if (error instanceof Error) {
        if (error.message.includes('timeout')) {
          alert('音声の読み込みがタイムアウトしました。もう一度お試しください。');
        } else {
          alert(error.message);
        }
      } else {
        alert('音声生成に失敗しました。');
      }
    } finally {
      setIsGeneratingAudio(false);
    }
  };

  const handleStopAudio = () => {
    if (audioRef.current) {
      try {
        // Remove event listeners to prevent conflicts
        audioRef.current.onplay = null;
        audioRef.current.onpause = null;
        audioRef.current.onended = null;
        audioRef.current.onerror = null;
        
        // Check if audio is not already paused/ended
        if (!audioRef.current.paused && !audioRef.current.ended) {
          audioRef.current.pause();
        }
        
        // Reset current time
        audioRef.current.currentTime = 0;
        console.log('🛑 Audio stopped');
      } catch (error) {
        console.warn('Warning stopping audio:', error);
      }
      
      // Clear the reference
      audioRef.current = null;
      setIsPlaying(false);
    }
  };

  // Cleanup audio resources on unmount or when audioUrl changes
  useEffect(() => {
    return () => {
      // Stop audio if playing
      handleStopAudio();
      
      // Clean up audio URL
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  // Additional cleanup on component unmount
  useEffect(() => {
    return () => {
      // Ensure audio is stopped and cleaned up
      if (audioRef.current) {
        try {
          if (!audioRef.current.paused) {
            audioRef.current.pause();
          }
          audioRef.current.src = '';
          audioRef.current.load();
        } catch (error) {
          console.warn('Warning during audio cleanup:', error);
        }
      }
      
      // Clean up any remaining audio URL
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-6 sm:py-8 px-4 sm:px-6 lg:px-8 fade-enter">
      <div className="max-w-4xl mx-auto">
        {/* Header - Responsive */}
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 mb-2">採点結果</h1>
          <p className="text-sm sm:text-base text-gray-600">あなたのスピーキング回答の評価です</p>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-t-xl shadow-md mb-0">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => handleTabChange('scores')}
              className={`flex-1 py-3 sm:py-4 px-4 sm:px-6 text-center text-sm sm:text-base font-semibold transition-colors duration-200 ${
                activeTab === 'scores'
                  ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              スコアとフィードバック
            </button>
            <button
              onClick={() => handleTabChange('model')}
              className={`flex-1 py-3 sm:py-4 px-4 sm:px-6 text-center text-sm sm:text-base font-semibold transition-colors duration-200 ${
                activeTab === 'model'
                  ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <span className="flex items-center justify-center gap-2">
                模範解答
                {isLoadingModel && !modelAnswer && (
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                {modelAnswer && !isLoadingModel && (
                  <svg className="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                )}
              </span>
            </button>
          </div>
        </div>

        {/* Tab Content with Slide Animation */}
        {activeTab === 'scores' ? (
          <div className={`${!isTransitioning ? (previousTab === 'model' ? 'slide-enter-left' : '') : ''}`}>
          <div className="space-y-4 sm:space-y-6">
            {/* Overall Score Card - Responsive */}
            <div className="bg-white rounded-b-xl shadow-lg p-6 sm:p-8 text-center">
          <p className="text-xs sm:text-sm text-gray-600 mb-2">総合スコア</p>
          <div className="flex items-center justify-center mb-4">
            <div className={`text-4xl sm:text-5xl md:text-6xl font-bold ${getScoreColor(scoringResult.overall_score).split(' ')[0]}`}>
              {scoringResult.overall_score.toFixed(1)}
            </div>
            <div className="text-2xl sm:text-3xl text-gray-400 ml-2">/ 4.0</div>
          </div>
          <div className={`inline-block px-3 sm:px-4 py-2 sm:py-3 rounded-lg border text-xs sm:text-sm max-w-md text-center ${getScoreColor(scoringResult.overall_score)}`}>
            <span className="font-semibold leading-tight">{getScoreLabel(scoringResult.overall_score)}</span>
          </div>
            </div>

            {/* User Transcript - Responsive */}
            <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">あなたの回答（文字起こし）</h3>
              <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                <p className="text-sm sm:text-base text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {scoringResult.user_transcript}
                </p>
              </div>
            </div>

            {/* Detailed Scores - Responsive */}
            {isTask1 ? (
              // Task 1: Show feedback categories without individual scores
              <div className="space-y-4 sm:space-y-6">
                {/* Delivery Feedback */}
                <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
                  <div className="mb-3 sm:mb-4">
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900">Delivery（発話）</h3>
                    <p className="text-xs sm:text-sm text-gray-600">流暢さ、発音、ペース、明瞭さ</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 sm:p-4">
                    <p className="text-sm sm:text-base text-gray-700 leading-relaxed">{scoringResult.delivery_feedback}</p>
                  </div>
                </div>

                {/* Language Use Feedback */}
                <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
                  <div className="mb-3 sm:mb-4">
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900">Language Use（言語使用）</h3>
                    <p className="text-xs sm:text-sm text-gray-600">文法、語彙、文構造</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 sm:p-4">
                    <p className="text-sm sm:text-base text-gray-700 leading-relaxed">{scoringResult.language_use_feedback}</p>
                  </div>
                </div>

                {/* Topic Development Feedback */}
                <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
                  <div className="mb-3 sm:mb-4">
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900">Topic Development（内容展開）</h3>
                    <p className="text-xs sm:text-sm text-gray-600">内容の関連性、詳細、構成、一貫性</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 sm:p-4">
                    <p className="text-sm sm:text-base text-gray-700 leading-relaxed">{scoringResult.topic_dev_feedback}</p>
                  </div>
                </div>

                {/* Strengths */}
                {scoringResult.strengths && scoringResult.strengths.length > 0 && (
                  <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">良い点</h3>
                    <ul className="space-y-2 sm:space-y-3">
                      {scoringResult.strengths.map((strength: string, index: number) => (
                        <li key={index} className="flex items-start">
                          <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 mr-2 sm:mr-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span className="text-sm sm:text-base text-gray-700">{strength}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              // Task 3: Show detailed scores for each criterion
              <div className="space-y-4 sm:space-y-6">
                {/* Delivery Score */}
                <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
                  <div className="flex items-center justify-between mb-3 sm:mb-4">
                    <div className="flex-1 min-w-0 pr-4">
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 truncate">Delivery（発話）</h3>
                      <p className="text-xs sm:text-sm text-gray-600">明瞭さ、流暢さ、発音、ペース</p>
                    </div>
                    <div className={`text-2xl sm:text-3xl font-bold flex-shrink-0 ${getScoreColor(scoringResult.delivery.score).split(' ')[0]}`}>
                      {scoringResult.delivery.score}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 sm:p-4">
                    <p className="text-sm sm:text-base text-gray-700 leading-relaxed">{scoringResult.delivery.feedback}</p>
                  </div>
                </div>

                {/* Language Use Score */}
                <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
                  <div className="flex items-center justify-between mb-3 sm:mb-4">
                    <div className="flex-1 min-w-0 pr-4">
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 truncate">Language Use（言語使用）</h3>
                      <p className="text-xs sm:text-sm text-gray-600">文法、語彙、文構造</p>
                    </div>
                    <div className={`text-2xl sm:text-3xl font-bold flex-shrink-0 ${getScoreColor(scoringResult.language_use.score).split(' ')[0]}`}>
                      {scoringResult.language_use.score}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 sm:p-4">
                    <p className="text-sm sm:text-base text-gray-700 leading-relaxed">{scoringResult.language_use.feedback}</p>
                  </div>
                </div>

                {/* Topic Development Score */}
                <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
                  <div className="flex items-center justify-between mb-3 sm:mb-4">
                    <div className="flex-1 min-w-0 pr-4">
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 truncate">Topic Development（内容展開）</h3>
                      <p className="text-xs sm:text-sm text-gray-600">内容の正確性、完全性、一貫性</p>
                    </div>
                    <div className={`text-2xl sm:text-3xl font-bold flex-shrink-0 ${getScoreColor(scoringResult.topic_development.score).split(' ')[0]}`}>
                      {scoringResult.topic_development.score}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 sm:p-4">
                    <p className="text-sm sm:text-base text-gray-700 leading-relaxed">{scoringResult.topic_development.feedback}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Improvement Tips - Responsive */}
            {scoringResult.improvement_tips.length > 0 && (
              <div className="bg-white rounded-xl shadow-md p-4 sm:p-6">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">改善アドバイス</h3>
            <ul className="space-y-2 sm:space-y-3">
              {scoringResult.improvement_tips.map((tip: string, index: number) => (
                <li key={index} className="flex items-start">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-600 mr-2 sm:mr-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm sm:text-base text-gray-700">{tip}</span>
                </li>
              ))}
            </ul>
              </div>
            )}

            {/* Disclaimer - Responsive */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 sm:p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-2 sm:ml-3">
              <p className="text-xs sm:text-sm text-yellow-800 font-medium">
                本採点はTOEFL本番基準に基づくAI評価です。ETSの公式スコアとは異なる場合があります
              </p>
            </div>
              </div>
            </div>
          </div>
          </div>
        ) : (
          <div className={`bg-white rounded-b-xl shadow-lg p-6 sm:p-8 ${!isTransitioning ? (previousTab === 'scores' ? 'slide-enter-right' : '') : ''}`}>
            {isLoadingModel ? (
              <div className="py-12">
                <LoadingSpinner message="模範解答を生成しています...（バックグラウンドで生成中）" />
                <p className="text-center text-sm text-gray-600 mt-4">
                  初回表示時は10-20秒ほどかかります
                </p>
              </div>
            ) : modelError ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <svg className="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-red-800 font-medium mb-2">エラーが発生しました</p>
                <p className="text-red-600 text-sm mb-4">{modelError}</p>
                <button
                  onClick={loadModelAnswer}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                >
                  再試行
                </button>
              </div>
            ) : modelAnswer ? (
              <div className="space-y-4 sm:space-y-6">
                {/* Model Answer Text - Responsive */}
                <div>
                  <h3 className="text-base sm:text-lg md:text-xl font-semibold text-gray-900 mb-3 sm:mb-4">模範解答</h3>
                  <div className="bg-gray-50 rounded-lg p-4 sm:p-6">
                    <p className="text-sm sm:text-base text-gray-800 leading-relaxed whitespace-pre-wrap">
                      {modelAnswer.model_answer}
                    </p>
                  </div>
                </div>

                {/* Custom Phrase Input - Responsive */}
                <div>
                  <h3 className="text-base sm:text-lg md:text-xl font-semibold text-gray-900 mb-3 sm:mb-4">カスタムフレーズを保存</h3>
                  <div className="bg-white border-2 border-gray-200 rounded-lg p-4">
                    <p className="text-sm text-gray-600 mb-3">模範解答から任意のフレーズをコピーして保存できます</p>
                    <div className="flex flex-col sm:flex-row gap-3">
                      <input
                        type="text"
                        value={customPhrase}
                        onChange={(e) => setCustomPhrase(e.target.value)}
                        placeholder="保存したいフレーズを入力..."
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            handleSaveCustomPhrase();
                          }
                        }}
                      />
                      <button
                        onClick={handleSaveCustomPhrase}
                        disabled={isSavingCustom || !customPhrase.trim()}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold"
                      >
                        {isSavingCustom ? '保存中...' : '保存'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Highlighted Phrases - Responsive */}
                {modelAnswer.highlighted_phrases.length > 0 && (
                  <div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4 mb-3 sm:mb-4">
                      <h3 className="text-base sm:text-lg md:text-xl font-semibold text-gray-900">AIが選んだ重要フレーズ</h3>
                      {saveMessage && (
                        <div className="bg-green-50 border border-green-200 rounded-lg px-3 sm:px-4 py-1.5 sm:py-2">
                          <p className="text-xs sm:text-sm text-green-800 font-medium">{saveMessage}</p>
                        </div>
                      )}
                    </div>
                    <div className="space-y-2 sm:space-y-3">
                      {modelAnswer.highlighted_phrases.map((phrase, index) => (
                        <div
                          key={index}
                          className="bg-white border-2 border-gray-200 rounded-lg p-3 sm:p-4 hover:border-indigo-300 transition-colors"
                        >
                          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4">
                            <div className="flex-1 min-w-0">
                              <p className="text-sm sm:text-base text-gray-900 font-medium mb-2">{phrase.text}</p>
                              {isTask1 && phrase.explanation && (
                                <p className="text-xs sm:text-sm text-gray-600 mb-2">{phrase.explanation}</p>
                              )}
                              <div className="flex flex-wrap gap-1.5 sm:gap-2">
                                <span className={`inline-block px-2 sm:px-3 py-0.5 sm:py-1 rounded-full text-xs font-semibold border ${getCategoryColor(phrase.category)}`}>
                                  {getCategoryLabel(phrase.category)}
                                </span>
                                {!isTask1 && phrase.useful_for_writing && (
                                  <span className="inline-block px-2 sm:px-3 py-0.5 sm:py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
                                    ✍️ Writingでも使えます
                                  </span>
                                )}
                              </div>
                            </div>
                            <button
                              onClick={() => handleSavePhrase(phrase, index)}
                              disabled={savingPhraseId === index || savedPhrases.has(index)}
                              className={`flex-shrink-0 w-full sm:w-auto px-3 sm:px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                                savedPhrases.has(index)
                                  ? 'bg-green-100 text-green-700 border-2 border-green-300 cursor-not-allowed'
                                  : 'bg-indigo-600 text-white hover:bg-indigo-700'
                              }`}
                            >
                              {savingPhraseId === index ? (
                                <span className="flex items-center justify-center gap-2">
                                  <svg className="animate-spin h-3 w-3 sm:h-4 sm:w-4" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                  保存中...
                                </span>
                              ) : savedPhrases.has(index) ? (
                                <span className="flex items-center justify-center gap-2">
                                  <svg className="w-3 h-3 sm:w-4 sm:h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                  </svg>
                                  保存済み
                                </span>
                              ) : (
                                '保存'
                              )}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Info Box - Responsive */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 sm:p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-4 w-4 sm:h-5 sm:w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-2 sm:ml-3">
                      <p className="text-xs sm:text-sm text-blue-800">
                        これらのフレーズは、スピーキングだけでなくライティングでも活用できます。保存して復習しましょう。
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* AI Review Section */}
        {showAIReview && aiReview && (
          <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8 mt-4 sm:mt-6 border-2 border-purple-200">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M9.504 1.132a1 1 0 01.992 0l1.75 1a1 1 0 11-.992 1.736L10 3.152l-1.254.716a1 1 0 11-.992-1.736l1.75-1zM5.618 4.504a1 1 0 01-.372 1.364L5.016 6l.23.132a1 1 0 11-.992 1.736L3 7.723V8a1 1 0 01-2 0V6a.996.996 0 01.52-.878l1.734-.99a1 1 0 011.364.372zm8.764 0a1 1 0 011.364-.372l1.734.99A.996.996 0 0118 6v2a1 1 0 11-2 0v-.277l-1.254.145a1 1 0 11-.992-1.736L14.984 6l-.23-.132a1 1 0 01-.372-1.364zm-7 4a1 1 0 011.364-.372L10 8.848l1.254-.716a1 1 0 11.992 1.736L11 10.723V12a1 1 0 11-2 0v-1.277l-1.246-.855a1 1 0 01-.372-1.364zM3 11a1 1 0 011 1v1.277l1.246.855a1 1 0 01-.372 1.364l-1.75-1A.996.996 0 013 14v-2a1 1 0 011-1zm14 0a1 1 0 011 1v2a.996.996 0 01-.52.878l-1.75 1a1 1 0 11-.992-1.736L15.984 14l-.23-.132a1 1 0 01.372-1.364L17 13.277V12a1 1 0 011-1zm-9.618 5.504a1 1 0 011.364.372l.254.145V16a1 1 0 112 0v1.021l.254-.145a1 1 0 11.992 1.736l-1.735.992a.995.995 0 01-1.022 0l-1.735-.992a1 1 0 01-.372-1.364z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-purple-900">AI添削結果</h3>
            </div>

            {/* User Transcript Display */}
            <div className="mb-6">
              <h4 className="text-base font-semibold text-gray-900 mb-3">あなたの回答（文字起こし）</h4>
              <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-blue-400">
                <p className="text-sm sm:text-base text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {scoringResult.user_transcript}
                </p>
              </div>
            </div>

            {/* AI Review Content */}
            <div className="space-y-4">
              {/* Strengths */}
              {aiReview.strengths && aiReview.strengths.length > 0 && (
                <div className="bg-green-50 rounded-lg p-4 border-l-4 border-green-400">
                  <h4 className="text-base font-semibold text-green-900 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    良い点
                  </h4>
                  <ul className="space-y-2">
                    {aiReview.strengths.map((strength: string, index: number) => (
                      <li key={index} className="text-sm text-green-800 flex items-start gap-2">
                        <span className="text-green-600 mt-1">•</span>
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Improvements */}
              {aiReview.improvements && aiReview.improvements.length > 0 && (
                <div className="bg-orange-50 rounded-lg p-4 border-l-4 border-orange-400">
                  <h4 className="text-base font-semibold text-orange-900 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    改善点
                  </h4>
                  <ul className="space-y-2">
                    {aiReview.improvements.map((improvement: string, index: number) => (
                      <li key={index} className="text-sm text-orange-800 flex items-start gap-2">
                        <span className="text-orange-600 mt-1">•</span>
                        <span>{improvement}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Specific Suggestions */}
              {aiReview.specific_suggestions && (
                <div className="bg-purple-50 rounded-lg p-4 border-l-4 border-purple-400">
                  <h4 className="text-base font-semibold text-purple-900 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                    </svg>
                    具体的な改善案
                  </h4>
                  <div className="text-sm text-purple-800 leading-relaxed whitespace-pre-wrap">
                    {aiReview.specific_suggestions}
                  </div>
                </div>
              )}

              {/* Score Improvement Tips */}
              {aiReview.score_improvement_tips && (
                <div className="bg-blue-50 rounded-lg p-4 border-l-4 border-blue-400">
                  <h4 className="text-base font-semibold text-blue-900 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
                    </svg>
                    スコアアップのコツ
                  </h4>
                  <div className="text-sm text-blue-800 leading-relaxed whitespace-pre-wrap">
                    {aiReview.score_improvement_tips}
                  </div>
                </div>
              )}

              {/* Improved Response */}
              {aiReview.improved_response && (
                <div className="bg-emerald-50 rounded-lg p-4 border-l-4 border-emerald-400">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-base font-semibold text-emerald-900 flex items-center gap-2">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414 1.414L10.586 9.5 9.293 10.793a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clipRule="evenodd" />
                      </svg>
                      改善版の回答例
                    </h4>
                    <button
                      onClick={() => handleGenerateAndPlayAudio(aiReview.improved_response)}
                      disabled={isGeneratingAudio}
                      className="flex items-center gap-2 px-3 py-1.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium shadow-sm"
                      title="改善版の回答を音声で聞く"
                    >
                      {isGeneratingAudio ? (
                        <>
                          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          生成中...
                        </>
                      ) : isPlaying ? (
                        <>
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" onClick={(e) => { e.stopPropagation(); handleStopAudio(); }}>
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                          停止
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                          </svg>
                          音声で聞く
                        </>
                      )}
                    </button>
                  </div>
                  <div className="text-sm text-emerald-800 leading-relaxed whitespace-pre-wrap bg-white rounded p-3 border border-emerald-200">
                    {aiReview.improved_response}
                  </div>
                  <div className="mt-2 space-y-1">
                    <p className="text-xs text-emerald-700">
                      💡 この改善版はあなたの回答の良い部分を活かしながら、より高いスコアが期待できるように調整されています。
                    </p>
                    <p className="text-xs text-emerald-600">
                      🔊 音声再生がブロックされる場合は、ページ内をクリックしてから再度お試しください。
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* AI Review Error */}
        {aiReviewError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{aiReviewError}</p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons - Responsive */}
        <div className="space-y-3 mt-4 sm:mt-6">
          {/* AI Review Button - Only show for individual task practice, not mock exam */}
          {!isMockExam && (
            <button
              onClick={handleAIReview}
              disabled={isLoadingAIReview}
              className="w-full bg-purple-600 text-white px-4 sm:px-6 py-3 rounded-lg text-sm sm:text-base font-semibold hover:bg-purple-700 transition-colors duration-200 shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoadingAIReview ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  AI添削を生成中...
                </>
              ) : showAIReview ? (
                <>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  AI添削を閉じる
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M9.504 1.132a1 1 0 01.992 0l1.75 1a1 1 0 11-.992 1.736L10 3.152l-1.254.716a1 1 0 11-.992-1.736l1.75-1zM5.618 4.504a1 1 0 01-.372 1.364L5.016 6l.23.132a1 1 0 11-.992 1.736L3 7.723V8a1 1 0 01-2 0V6a.996.996 0 01.52-.878l1.734-.99a1 1 0 011.364.372zm8.764 0a1 1 0 011.364-.372l1.734.99A.996.996 0 0118 6v2a1 1 0 11-2 0v-.277l-1.254.145a1 1 0 11-.992-1.736L14.984 6l-.23-.132a1 1 0 01-.372-1.364zm-7 4a1 1 0 011.364-.372L10 8.848l1.254-.716a1 1 0 11.992 1.736L11 10.723V12a1 1 0 11-2 0v-1.277l-1.246-.855a1 1 0 01-.372-1.364zM3 11a1 1 0 011 1v1.277l1.246.855a1 1 0 01-.372 1.364l-1.75-1A.996.996 0 013 14v-2a1 1 0 011-1zm14 0a1 1 0 011 1v2a.996.996 0 01-.52.878l-1.75 1a1 1 0 11-.992-1.736L15.984 14l-.23-.132a1 1 0 01.372-1.364L17 13.277V12a1 1 0 011-1zm-9.618 5.504a1 1 0 011.364.372l.254.145V16a1 1 0 112 0v1.021l.254-.145a1 1 0 11.992 1.736l-1.735.992a.995.995 0 01-1.022 0l-1.735-.992a1 1 0 01-.372-1.364z" clipRule="evenodd" />
                  </svg>
                  回答をAIで添削
                </>
              )}
            </button>
          )}

          {/* Other Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
            <button
              onClick={handlePracticeAgain}
              className="flex-1 bg-indigo-600 text-white px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg text-sm sm:text-base font-semibold hover:bg-indigo-700 transition-colors duration-200 shadow-md"
            >
              もう一度練習
            </button>
          <button
            onClick={handleReturnHome}
            className="flex-1 bg-white text-gray-700 px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg text-sm sm:text-base font-semibold border-2 border-gray-300 hover:bg-gray-50 transition-colors duration-200"
          >
            ホームに戻る
          </button>
          </div>
        </div>
      </div>
    </div>
  );
}
