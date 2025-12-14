/**
 * WaveformVisualizer component - Real-time audio waveform visualization
 * 
 * Features:
 * - Real-time audio level visualization using Web Audio API
 * - Canvas-based waveform rendering
 * - Responsive design
 * 
 * Requirements: 4.2
 */

'use client';

import { useEffect, useRef } from 'react';

interface WaveformVisualizerProps {
  audioStream: MediaStream | null;
  isRecording: boolean;
}

export default function WaveformVisualizer({
  audioStream,
  isRecording,
}: WaveformVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array<ArrayBuffer> | null>(null);

  useEffect(() => {
    if (!audioStream || !isRecording) {
      // Clean up when not recording
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      
      // Clear canvas
      if (canvasRef.current) {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
      }
      
      return;
    }

    // Set up Web Audio API
    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(audioStream);

    analyser.fftSize = 2048;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength) as Uint8Array<ArrayBuffer>;

    source.connect(analyser);

    audioContextRef.current = audioContext;
    analyserRef.current = analyser;
    dataArrayRef.current = dataArray;

    // Start visualization
    draw();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audioStream, isRecording]);

  const draw = () => {
    if (!canvasRef.current || !analyserRef.current || !dataArrayRef.current) {
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const analyser = analyserRef.current;
    const dataArray = dataArrayRef.current;
    const bufferLength = dataArray.length;

    animationFrameRef.current = requestAnimationFrame(draw);

    analyser.getByteTimeDomainData(dataArray);

    // Clear canvas
    ctx.fillStyle = '#f3f4f6';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw waveform
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#3b82f6';
    ctx.beginPath();

    const sliceWidth = (canvas.width * 1.0) / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * canvas.height) / 2;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();
  };

  return (
    <div className="w-full max-w-2xl">
      <canvas
        ref={canvasRef}
        width={800}
        height={200}
        className="w-full h-32 bg-gray-100 rounded-lg border border-gray-300"
        aria-label="音声波形"
      />
      {!isRecording && (
        <div className="flex items-center justify-center h-32 bg-gray-100 rounded-lg border border-gray-300 -mt-32">
          <p className="text-sm text-gray-500">録音待機中...</p>
        </div>
      )}
    </div>
  );
}
