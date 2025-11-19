/**
 * Custom hook for setting document title (SEO)
 * Updates the page title in the browser tab
 */
import { useEffect } from 'react';

export function useDocumentTitle(title) {
  useEffect(() => {
    if (title) {
      document.title = title;
    }

    // Cleanup: restore default title when component unmounts
    return () => {
      document.title = 'FDA Drug Approval Tracker';
    };
  }, [title]);
}
