import { useEffect, useState } from 'react';
import { getFeedbackPage, type FeedbackListItem } from '@shared/api/feedback/getFeedbackList';

export const useFeedbackList = () => {
  const [items, setItems] = useState<FeedbackListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState({ search: '', author: '', sortBy: 'created_at', sortOrder: 'desc', page: 0, pageSize: 20 });
  const [total, setTotal] = useState(0);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const reload = () => setRevision((n) => n + 1);
    window.addEventListener('focus', reload);
    window.addEventListener('feedback:created', reload);
    return () => { window.removeEventListener('focus', reload); window.removeEventListener('feedback:created', reload); };
  }, []);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const list = await getFeedbackPage(query);
        if (isMounted) {
          setItems(list.items);
          setTotal(list.total);
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
  }, [query, revision]);

  return { items, isLoading, error, query, setQuery, total, reload: () => setRevision((n) => n + 1) };
};
