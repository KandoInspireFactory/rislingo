/**
 * LoadingSpinner component - Reusable loading indicator
 */

interface LoadingSpinnerProps {
  message?: string;
}

export default function LoadingSpinner({ message = '読み込み中...' }: LoadingSpinnerProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">{message}</p>
      </div>
    </div>
  );
}
