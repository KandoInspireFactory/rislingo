/**
 * AudioRecorder component - Audio recording with real-time waveform visualization
 * 
 * Features:
 * - MediaRecorder API for audio recording
 * - Real-time waveform visualization
 * - Microphone access error handling
 * - Automatic recording start and stop
 * 
 * Requirements: 4.1, 4.2
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import WaveformVisualizer from './WaveformVisualizer';
import { RecordingError } from '@/lib/api-client';

interface AudioRecorderProps {
  duration: number; // Recording duration in seconds
  onRecordingComplete: (audioBlob: Blob) => void;
  onError: (error: Error) => void;
  autoStart?: boolean; // Automatically start recording on mount
}

export default function AudioRecorder({
  duration,
  onRecordingComplete,
  onError,
  autoStart = false,
}: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mimeTypeRef = useRef<string>('audio/webm');

  // Start recording function
  const startRecording = async () => {
    try {
      // Request microphone access with optimal settings
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        },
      });

      setAudioStream(stream);
      audioChunksRef.current = [];

      // Create MediaRecorder instance with fallback MIME types
      let mimeType = 'audio/webm';
      if (!MediaRecorder.isTypeSupported('audio/webm')) {
        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
          mimeType = 'audio/webm;codecs=opus';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        } else if (MediaRecorder.isTypeSupported('audio/wav')) {
          mimeType = 'audio/wav';
        } else {
          // Use default (browser will choose)
          mimeType = '';
        }
      }

      console.log('🎙️ Using MIME type:', mimeType);
      mimeTypeRef.current = mimeType;
      
      const mediaRecorder = new MediaRecorder(stream, mimeType ? {
        mimeType: mimeType,
      } : {});

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        console.log('🎙️ MediaRecorder stopped. Chunks collected:', audioChunksRef.current.length);
        
        if (audioChunksRef.current.length === 0) {
          console.error('❌ No audio chunks collected!');
          const error = new RecordingError('録音データが収集されませんでした。');
          setError(error.message);
          onError(error);
          return;
        }
        
        const audioBlob = new Blob(audioChunksRef.current, {
          type: mimeTypeRef.current,
        });
        console.log('📦 Audio blob created. Size:', audioBlob.size, 'bytes, Type:', audioBlob.type);
        
        // Clean up stream first
        stream.getTracks().forEach((track) => track.stop());
        setAudioStream(null);
        setIsRecording(false);
        
        // Then trigger completion callback
        onRecordingComplete(audioBlob);
      };

      mediaRecorder.onerror = () => {
        const error = new RecordingError('録音中にエラーが発生しました。');
        setError(error.message);
        onError(error);
      };

      mediaRecorderRef.current = mediaRecorder;
      // Start recording with timeslice to collect data periodically (every 100ms)
      mediaRecorder.start(100);
      setIsRecording(true);
      setError(null);
      console.log('🎙️ Recording started');

      // Auto-stop after duration
      console.log(`⏱️ Recording will auto-stop in ${duration} seconds`);
      recordingTimeoutRef.current = setTimeout(() => {
        console.log('⏰ Auto-stop timeout triggered');
        stopRecording();
      }, duration * 1000);
    } catch (err) {
      handleRecordingError(err);
    }
  };

  // Stop recording function
  const stopRecording = () => {
    console.log('🛑 stopRecording called. mediaRecorder state:', mediaRecorderRef.current?.state);
    
    if (!mediaRecorderRef.current) {
      console.warn('⚠️ No mediaRecorder instance');
      return;
    }
    
    // Check if mediaRecorder is in a valid state to stop
    if (mediaRecorderRef.current.state === 'recording') {
      console.log('⏹️ Stopping MediaRecorder...');
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    } else if (mediaRecorderRef.current.state === 'paused') {
      console.log('⏸️ MediaRecorder is paused, resuming and stopping...');
      mediaRecorderRef.current.resume();
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    } else {
      console.warn('⚠️ MediaRecorder is not in recording state:', mediaRecorderRef.current.state);
      // If not recording but we have chunks, still trigger completion
      if (audioChunksRef.current.length > 0) {
        console.log('📦 Manually triggering completion with existing chunks');
        const audioBlob = new Blob(audioChunksRef.current, {
          type: mimeTypeRef.current,
        });
        onRecordingComplete(audioBlob);
        setIsRecording(false);
        
        // Clean up stream
        if (audioStream) {
          audioStream.getTracks().forEach((track) => track.stop());
          setAudioStream(null);
        }
      }
    }
    
    // Clear timeout
    if (recordingTimeoutRef.current) {
      clearTimeout(recordingTimeoutRef.current);
      recordingTimeoutRef.current = null;
    }
  };

  // Handle recording errors
  const handleRecordingError = (err: unknown) => {
    let errorMessage = '音声録音の開始に失敗しました。';
    
    if (err instanceof DOMException) {
      if (err.name === 'NotAllowedError') {
        errorMessage = 'マイクへのアクセスが拒否されました。ブラウザの設定を確認してください。';
      } else if (err.name === 'NotFoundError') {
        errorMessage = 'マイクが見つかりません。デバイスを確認してください。';
      } else if (err.name === 'NotReadableError') {
        errorMessage = 'マイクが他のアプリケーションで使用中です。';
      } else if (err.name === 'OverconstrainedError') {
        errorMessage = 'マイクの設定が対応していません。';
      }
    }
    
    setError(errorMessage);
    onError(new RecordingError(errorMessage));
  };

  // Auto-start recording if enabled
  useEffect(() => {
    if (autoStart) {
      startRecording();
    }

    // Cleanup on unmount
    return () => {
      if (recordingTimeoutRef.current) {
        clearTimeout(recordingTimeoutRef.current);
      }
      if (audioStream) {
        audioStream.getTracks().forEach((track) => track.stop());
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoStart]);

  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      {/* Recording indicator */}
      {isRecording && (
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
          <span className="text-sm font-medium text-gray-700">録音中...</span>
        </div>
      )}

      {/* Waveform visualizer */}
      <WaveformVisualizer audioStream={audioStream} isRecording={isRecording} />

      {/* Error message */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Manual controls (if not auto-start) */}
      {!autoStart && (
        <div className="flex space-x-4">
          {!isRecording ? (
            <button
              onClick={startRecording}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              録音開始
            </button>
          ) : (
            <button
              onClick={stopRecording}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              録音停止
            </button>
          )}
        </div>
      )}
    </div>
  );
}
