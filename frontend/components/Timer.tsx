/**
 * Timer component - Countdown timer
 * 
 * Features:
 * - Countdown functionality
 * - Callback function on timer completion
 * - Large font size (48-64px) for high visibility
 * 
 * Requirements: 3.1, 3.3, 3.4, 3.5, 10.3
 */

'use client';

import { useEffect, useState } from 'react';

interface TimerProps {
  duration: number; // Duration in seconds
  onComplete: () => void; // Callback when timer reaches 0
  warningThreshold?: number; // Legacy prop (no longer used)
}

export default function Timer({ 
  duration, 
  onComplete, 
  warningThreshold = 15 // Legacy prop, kept for compatibility
}: TimerProps) {
  const [timeRemaining, setTimeRemaining] = useState(duration);

  // Countdown logic
  useEffect(() => {
    if (timeRemaining <= 0) {
      onComplete();
      return;
    }

    const intervalId = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(intervalId);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(intervalId);
  }, [timeRemaining, onComplete]);

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <div
        className="text-6xl font-bold text-gray-800"
        style={{ fontSize: '56px' }} // 48-64px range
        role="timer"
        aria-live="polite"
        aria-atomic="true"
      >
        {formatTime(timeRemaining)}
      </div>
    </div>
  );
}
