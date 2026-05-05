import { useEffect, useState } from 'react';
import { getFeedbackList, type FeedbackListItem } from '@shared/api/feedback/getFeedbackList';

export const useFeedbackList = () => {
  const [items, setItems] = useState<FeedbackListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const list = await getFeedbackList();
        if (isMounted) {
          setItems(list);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(loadError instanceof Error ? loadError.message : 'Не удалось загрузить обратную связь');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void load();

    return () => {
      isMounted = false;
    };
  }, []);

  return { items, isLoading, error };
};
