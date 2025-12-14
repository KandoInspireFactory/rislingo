'use client';

import { useRouter } from 'next/navigation';

export default function BackButton() {
  const router = useRouter();

  const handleBack = () => {
    router.push('/home');
  };

  return (
    <button
      onClick={handleBack}
      className="flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-300 hover:bg-white/5"
      style={{ color: 'var(--foreground-muted)' }}
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
      </svg>
      <span className="text-sm font-medium">戻る</span>
    </button>
  );
}