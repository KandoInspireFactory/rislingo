/**
 * ErrorScreen - Reusable error display component
 * 
 * Displays error messages with consistent styling across all pages.
 * Supports different error types with appropriate icons and actions.
 */

'use client';

import { useRouter } from 'next/navigation';
import LoadingSpinner from './LoadingSpinner';
import { 
  APIError, 
  NetworkError, 
  RateLimitError, 
  ServerError, 
  AuthenticationError,
  ValidationError,
  RecordingError
} from '@/lib/api-client';

interface ErrorScreenProps {
  error: string | Error;
  showLoading?: boolean;
  onRetry?: () => void;
  showHomeButton?: boolean;
}

export default function ErrorScreen({ 
  error, 
  showLoading = false,
  onRetry,
  showHomeButton = true
}: ErrorScreenProps) {
  const router = useRouter();

  const handleBackToHome = () => {
    router.push('/home');
  };

  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    }
  };

  if (showLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  // Determine error type and get appropriate message
  let errorMessage: string;
  let errorType: 'network' | 'auth' | 'rate-limit' | 'validation' | 'recording' | 'server' | 'generic' = 'generic';
  let errorDetails: Record<string, unknown> | undefined;

  if (error instanceof NetworkError) {
    errorMessage = error.message;
    errorType = 'network';
  } else if (error instanceof AuthenticationError) {
    errorMessage = error.userMessage;
    errorType = 'auth';
  } else if (error instanceof RateLimitError) {
    errorMessage = error.userMessage;
    errorType = 'rate-limit';
  } else if (error instanceof ValidationError) {
    errorMessage = error.userMessage;
    errorType = 'validation';
    errorDetails = error.details;
  } else if (error instanceof RecordingError) {
    errorMessage = error.message;
    errorType = 'recording';
  } else if (error instanceof ServerError) {
    errorMessage = error.userMessage;
    errorType = 'server';
  } else if (error instanceof APIError) {
    errorMessage = error.userMessage;
    errorType = 'generic';
    errorDetails = error.details as Record<string, unknown> | undefined;
  } else if (error instanceof Error) {
    errorMessage = error.message;
    errorType = 'generic';
  } else {
    errorMessage = String(error);
    errorType = 'generic';
  }

  // Get icon and color based on error type
  const getErrorIcon = () => {
    switch (errorType) {
      case 'network':
        return (
          <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
          </svg>
        );
      case 'auth':
        return (
          <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        );
      case 'rate-limit':
        return (
          <svg className="w-8 h-8 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'recording':
        return (
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        );
      default:
        return (
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
    }
  };

  const getIconBgColor = () => {
    switch (errorType) {
      case 'network':
        return 'bg-orange-100';
      case 'auth':
        return 'bg-yellow-100';
      case 'rate-limit':
        return 'bg-amber-100';
      case 'recording':
        return 'bg-red-100';
      default:
        return 'bg-red-100';
    }
  };

  // Show retry button for network and server errors
  const showRetryButton = (errorType === 'network' || errorType === 'server') && onRetry;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-xl shadow-md p-8">
          <div className={`w-16 h-16 ${getIconBgColor()} rounded-full flex items-center justify-center mx-auto mb-4`}>
            {getErrorIcon()}
          </div>
          
          <h2 className="text-xl font-semibold text-gray-900 mb-2 text-center">
            {errorType === 'network' && 'ネットワークエラー'}
            {errorType === 'auth' && '認証エラー'}
            {errorType === 'rate-limit' && 'リクエスト制限'}
            {errorType === 'validation' && '入力エラー'}
            {errorType === 'recording' && '録音エラー'}
            {errorType === 'server' && 'サーバーエラー'}
            {errorType === 'generic' && 'エラー'}
          </h2>
          
          <p className="text-gray-600 mb-6 text-center">{errorMessage}</p>

          {/* Show validation details if available */}
          {errorType === 'validation' && errorDetails?.validation_errors && Array.isArray(errorDetails.validation_errors) && errorDetails.validation_errors.length > 0 ? (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700 mb-2">詳細:</p>
              <ul className="text-sm text-gray-600 space-y-1">
                {(errorDetails.validation_errors as Array<{ field: string; message: string }>).map((err, idx) => (
                  <li key={idx}>• {String(err.field)}: {String(err.message)}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="space-y-3">
            {showRetryButton && (
              <button
                onClick={handleRetry}
                className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
              >
                再試行
              </button>
            )}
            
            {showHomeButton && (
              <button
                onClick={handleBackToHome}
                className={`w-full py-3 px-4 rounded-lg transition-colors font-medium ${
                  showRetryButton 
                    ? 'bg-gray-100 text-gray-700 hover:bg-gray-200' 
                    : 'bg-indigo-600 text-white hover:bg-indigo-700'
                }`}
              >
                ホームに戻る
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
