/**
 * useProblemData - Custom hook for loading problem data from URL params
 * 
 * Handles problem data parsing and error states consistently across all practice phases
 */

'use client';

import { useEffect, useState, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { Problem } from '@/lib/types';

interface UseProblemDataReturn {
  problem: Problem | null;
  isLoading: boolean;
  error: string | null;
}

export function useProblemData(): UseProblemDataReturn {
  const searchParams = useSearchParams();
  const [problem, setProblem] = useState<Problem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    // Prevent duplicate execution in React Strict Mode
    if (hasLoadedRef.current) {
      return;
    }
    
    const safeParseProblemData = (data: string, source: string) => {
      try {
        if (!data || data === 'undefined' || data === 'null') {
          console.warn(`⚠️ Invalid problem data from ${source}:`, data);
          return null;
        }
        
        const parsed = JSON.parse(data);
        if (!parsed || !parsed.problem_id) {
          console.warn(`⚠️ Problem data missing required fields from ${source}:`, parsed);
          return null;
        }
        
        return parsed;
      } catch (err) {
        console.error(`❌ Failed to parse problem data from ${source}:`, err);
        return null;
      }
    };

    try {
      // First try to get problem data from URL params
      const problemData = searchParams.get('problem');
      
      if (problemData) {
        console.log('📖 Loading problem data from URL params');
        const decodedData = decodeURIComponent(problemData);
        const parsedProblem = safeParseProblemData(decodedData, 'URL');
        
        if (parsedProblem) {
          setProblem(parsedProblem);
          hasLoadedRef.current = true;
        } else {
          // Try session storage as fallback
          console.log('🔄 Invalid URL data, trying session storage...');
          const sessionData = sessionStorage.getItem('currentProblem');
          const sessionProblem = safeParseProblemData(sessionData || '', 'sessionStorage');
          
          if (sessionProblem) {
            console.log('✅ Problem data found in session storage');
            setProblem(sessionProblem);
            hasLoadedRef.current = true;
          } else {
            console.warn('⚠️ No valid problem data found');
            setError('問題データが見つかりません。');
          }
        }
      } else {
        // If no URL params, try session storage
        console.log('📖 Trying to load problem data from session storage');
        const sessionData = sessionStorage.getItem('currentProblem');
        const sessionProblem = safeParseProblemData(sessionData || '', 'sessionStorage');
        
        if (sessionProblem) {
          console.log('✅ Problem data found in session storage');
          setProblem(sessionProblem);
          hasLoadedRef.current = true;
        } else {
          console.warn('⚠️ No problem data found in URL params or session storage');
          setError('問題データが見つかりません。');
        }
      }
    } catch (err) {
      console.error('❌ Unexpected error loading problem data:', err);
      setError('問題データの読み込みに失敗しました。');
    } finally {
      setIsLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 空の依存配列でマウント時のみ実行

  return { problem, isLoading, error };
}
