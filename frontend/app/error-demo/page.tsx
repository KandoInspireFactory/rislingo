/**
 * Error Demo Page - Demonstrates error handling components
 * 
 * This page is for testing and demonstration purposes only.
 */

'use client';

import { useState } from 'react';
import ErrorScreen from '@/components/ErrorScreen';
import ErrorMessage from '@/components/ErrorMessage';
import { 
  APIError, 
  NetworkError, 
  RateLimitError, 
  ServerError,
  AuthenticationError,
  ValidationError,
  RecordingError
} from '@/lib/api-client';

export default function ErrorDemoPage() {
  const [selectedError, setSelectedError] = useState<Error | null>(null);
  const [showFullScreen, setShowFullScreen] = useState(false);

  const errors = [
    { name: 'Network Error', error: new NetworkError() },
    { name: 'Authentication Error', error: new AuthenticationError() },
    { name: 'Rate Limit Error', error: new RateLimitError() },
    { name: 'Server Error', error: new ServerError() },
    { name: 'Validation Error', error: new ValidationError('入力データが正しくありません。', { validation_errors: [{ field: 'email', message: 'Invalid email format' }] }) },
    { name: 'Recording Error', error: new RecordingError('マイクへのアクセスが拒否されました。') },
    { name: 'Generic API Error', error: new APIError('Something went wrong', 'GENERIC_ERROR', 'エラーが発生しました。') },
  ];

  const handleRetry = () => {
    setSelectedError(null);
  };

  if (showFullScreen && selectedError) {
    return <ErrorScreen error={selectedError} onRetry={handleRetry} />;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Error Handling Demo</h1>
        
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Error Types</h2>
          <p className="text-gray-600 mb-6">
            Click on an error type to see how it&apos;s displayed:
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {errors.map((item, index) => (
              <button
                key={index}
                onClick={() => {
                  setSelectedError(item.error);
                  setShowFullScreen(false);
                }}
                className="p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-colors text-left"
              >
                <span className="font-medium text-gray-900">{item.name}</span>
              </button>
            ))}
          </div>

          {selectedError && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Inline Display:</h3>
                <button
                  onClick={() => setShowFullScreen(true)}
                  className="text-sm text-indigo-600 hover:text-indigo-700"
                >
                  View Full Screen →
                </button>
              </div>
              <ErrorMessage error={selectedError} onDismiss={() => setSelectedError(null)} />
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Implementation Details</h2>
          <div className="space-y-4 text-sm text-gray-600">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Backend Error Format:</h3>
              <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto">
{`{
  "error": {
    "code": "ERROR_CODE",
    "message": "Technical message",
    "user_message": "User-friendly message",
    "details": {}
  }
}`}
              </pre>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Error Types:</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>NetworkError - Connection issues</li>
                <li>AuthenticationError - Login failures</li>
                <li>RateLimitError - Too many requests</li>
                <li>ServerError - Server-side issues</li>
                <li>ValidationError - Invalid input data</li>
                <li>RecordingError - Microphone access issues</li>
                <li>APIError - Generic API errors</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
