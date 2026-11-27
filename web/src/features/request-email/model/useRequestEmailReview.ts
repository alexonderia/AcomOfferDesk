import { useEffect, useRef, useState } from 'react';
import type { RequestEmailPreview } from '@shared/api/requests/previewRequestEmails';

export const useRequestEmailReview = <T,>(scopeKey?: string | number) => {
  const [review, setReview] = useState<{ snapshot: T; preview: RequestEmailPreview; fontStyles: string } | null>(null);
  const [isLoadingReview, setIsLoadingReview] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setReview(null);
    setIsLoadingReview(false);
    return () => {
      controllerRef.current?.abort();
      controllerRef.current = null;
    };
  }, [scopeKey]);

  const prepareReview = async (snapshot: T, load: (signal: AbortSignal) => Promise<RequestEmailPreview | { preview: RequestEmailPreview; snapshot: T }>) => {
    if (controllerRef.current) return;
    const controller = new AbortController();
    controllerRef.current = controller;
    setIsLoadingReview(true);
    try {
      const [result, { documentFontStyles }] = await Promise.all([load(controller.signal), import('@shared/theme/documentFonts')]);
      const prepared = 'preview' in result ? result : { snapshot, preview: result };
      if (!controller.signal.aborted) setReview({ ...prepared, fontStyles: documentFontStyles });
    } finally {
      if (!controller.signal.aborted) setIsLoadingReview(false);
      if (controllerRef.current === controller) controllerRef.current = null;
    }
  };

  return { review, isLoadingReview, prepareReview, closeReview: () => setReview(null) };
};
