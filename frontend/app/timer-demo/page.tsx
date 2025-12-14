/**
 * Timer Demo Page - For testing Timer component functionality
 */

'use client';

import { useState } from 'react';
import Timer from '@/components/Timer';

export default function TimerDemoPage() {
  const [isTimerActive, setIsTimerActive] = useState(false);
  const [duration, setDuration] = useState(30);
  const [key, setKey] = useState(0);

  const handleComplete = () => {
    alert('タイマー終了！');
    setIsTimerActive(false);
  };

  const startTimer = () => {
    setKey((prev) => prev + 1); // Force remount to restart timer
    setIsTimerActive(true);
  };

  const resetTimer = () => {
    setIsTimerActive(false);
    setKey((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          タイマーコンポーネント デモ
        </h1>

        {isTimerActive ? (
          <div className="mb-8">
            <Timer key={key} duration={duration} onComplete={handleComplete} />
          </div>
        ) : (
          <div className="mb-8 text-center text-gray-500">
            タイマーを開始してください
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              時間設定（秒）
            </label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              disabled={isTimerActive}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-100"
              min="1"
              max="300"
            />
          </div>

          <div className="flex gap-4">
            <button
              onClick={startTimer}
              disabled={isTimerActive}
              className="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              開始
            </button>
            <button
              onClick={resetTimer}
              className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors"
            >
              リセット
            </button>
          </div>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <h2 className="text-sm font-semibold text-blue-800 mb-2">機能説明</h2>
          <ul className="text-xs text-blue-700 space-y-1">
            <li>• カウントダウン機能</li>
            <li>• 残り15秒以下で警告表示（オレンジ色）</li>
            <li>• タイマー終了時にコールバック実行</li>
            <li>• 48-64pxの大きなフォントサイズ</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
