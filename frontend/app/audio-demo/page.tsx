/**
 * Audio Recorder Demo Page
 * 
 * This page demonstrates the AudioRecorder component functionality
 */

'use client';

import { useState } from 'react';
import AudioRecorder from '@/components/AudioRecorder';

export default function AudioDemoPage() {
  const [recordedAudio, setRecordedAudio] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);

  const handleRecordingComplete = (audioBlob: Blob) => {
    setRecordedAudio(audioBlob);
    const url = URL.createObjectURL(audioBlob);
    setAudioUrl(url);
    setIsRecording(false);
  };

  const handleError = (err: Error) => {
    setError(err.message);
    setIsRecording(false);
    console.error('Recording error:', err);
  };

  const startNewRecording = () => {
    setRecordedAudio(null);
    setAudioUrl(null);
    setError(null);
    setIsRecording(true);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
          音声録音デモ
        </h1>

        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            録音テスト（10秒）
          </h2>
          
          {!isRecording ? (
            <button
              onClick={startNewRecording}
              className="mb-6 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              録音を開始
            </button>
          ) : (
            <div className="mb-6">
              <AudioRecorder
                duration={10}
                onRecordingComplete={handleRecordingComplete}
                onError={handleError}
                autoStart={true}
              />
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 font-medium">エラー:</p>
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {audioUrl && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-700 font-medium mb-2">録音完了！</p>
              <audio controls src={audioUrl} className="w-full">
                Your browser does not support the audio element.
              </audio>
              <p className="text-sm text-gray-600 mt-2">
                ファイルサイズ: {recordedAudio ? (recordedAudio.size / 1024).toFixed(2) : 0} KB
              </p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            手動録音テスト
          </h2>
          <AudioRecorder
            duration={60}
            onRecordingComplete={(blob) => {
              const url = URL.createObjectURL(blob);
              setAudioUrl(url);
              setRecordedAudio(blob);
            }}
            onError={handleError}
            autoStart={false}
          />
        </div>

        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            使用方法
          </h3>
          <ul className="list-disc list-inside text-blue-800 space-y-1">
            <li>「録音を開始」ボタンをクリックして10秒間の自動録音を開始</li>
            <li>マイクへのアクセスを許可してください</li>
            <li>録音中はリアルタイムで音声波形が表示されます</li>
            <li>録音完了後、音声を再生できます</li>
            <li>手動録音セクションでは、開始・停止を手動で制御できます</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
