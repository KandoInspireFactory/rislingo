/**
 * ErrorMessage - Inline error message component
 * 
 * Displays error messages inline within forms or sections
 */

'use client';

import { 
  APIError, 
  NetworkError, 
  RateLimitError, 
  RecordingError 
} from '@/lib/api-client';

interface ErrorMessageProps {
  error: string | Error;
  className?: string;
  onDismiss?: () => void;
}

export default function ErrorMessage({ error, className = '', onDismiss }: ErrorMessageProps) {
  // Determine error message
  let errorMessage: string;
  let errorType: 'network' | 'rate-limit' | 'recording' | 'generic' = 'generic';

  if (error instanceof NetworkError) {
    errorMessage = error.message;
    errorType = 'network';
  } else if (error instanceof RateLimitError) {
    errorMessage = error.userMessage;
    errorType = 'rate-limit';
  } else if (error instanceof RecordingError) {
    errorMessage = error.message;
    errorType = 'recording';
  } else if (error instanceof APIError) {
    errorMessage = error.userMessage;
    errorType = 'generic';
  } else if (error instanceof Error) {
    errorMessage = error.message;
    errorType = 'generic';
  } else {
    errorMessage = String(error);
    errorType = 'generic';
  }

  // Get icon based on error type
  const getIcon = () => {
    switch (errorType) {
      case 'network':
        return (
          <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
          </svg>
        );
      case 'rate-limit':
        return (
          <svg className="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'recording':
        return (
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  // Get background color based on error type
  const getBgColor = () => {
    switch (errorType) {
      case 'network':
        return 'bg-orange-50 border-orange-200';
      case 'rate-limit':
        return 'bg-amber-50 border-amber-200';
      case 'recording':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-red-50 border-red-200';
    }
  };

  const getTextColor = () => {
    switch (errorType) {
      case 'network':
        return 'text-orange-800';
      case 'rate-limit':
        return 'text-amber-800';
      case 'recording':
        return 'text-red-800';
      default:
        return 'text-red-800';
    }
  };

  return (
    <div className={`flex items-start space-x-3 p-4 border rounded-lg ${getBgColor()} ${className}`}>
      <div className="flex-shrink-0 mt-0.5">
        {getIcon()}
      </div>
      <div className="flex-1">
        <p className={`text-sm font-medium ${getTextColor()}`}>
          {errorMessage}
        </p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className={`flex-shrink-0 ${getTextColor()} hover:opacity-70 transition-opacity`}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}
