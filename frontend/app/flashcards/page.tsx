'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';
import LoadingSpinner from '@/components/LoadingSpinner';

/**
 * Flashcards main page - redirects to selection page
 */
export default function FlashcardsPage() {
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      const authenticated = await isAuthenticated();
      if (!authenticated) {
        router.push('/login');
      } else {
        // Redirect to selection page
        router.push('/flashcards/select');
      }
    };

    checkAuth();
  }, [router]);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return null;
}
