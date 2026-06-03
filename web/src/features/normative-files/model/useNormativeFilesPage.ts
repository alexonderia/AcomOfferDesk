import { useCallback, useEffect, useState } from 'react';
import {
  getNormativeFiles,
  updateNormativeFileStatus,
  type NormativeFileItem,
  type NormativeFileStatus,
} from '@shared/api/normative';

export const useNormativeFilesPage = () => {
  const [items, setItems] = useState<NormativeFileItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingIds, setUpdatingIds] = useState<Set<number>>(new Set());

  const loadItems = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const nextItems = await getNormativeFiles();
      setItems(nextItems);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Не удалось загрузить нормативные документы');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadItems();
  }, [loadItems]);

  const handleStatusChange = useCallback(async (item: NormativeFileItem, nextStatus: NormativeFileStatus) => {
    if (item.status === nextStatus) {
      return;
    }

    const previousStatus = item.status;
    setItems((current) =>
      current.map((row) => (row.id === item.id ? { ...row, status: nextStatus } : row))
    );
    setUpdatingIds((current) => new Set(current).add(item.id));

    try {
      const updated = await updateNormativeFileStatus(item.id, nextStatus);
      setItems((current) => current.map((row) => (row.id === item.id ? updated : row)));
    } catch (updateError) {
      setItems((current) =>
        current.map((row) => (row.id === item.id ? { ...row, status: previousStatus } : row))
      );
      throw updateError;
    } finally {
      setUpdatingIds((current) => {
        const next = new Set(current);
        next.delete(item.id);
        return next;
      });
    }
  }, []);

  return {
    items,
    isLoading,
    error,
    updatingIds,
    reload: loadItems,
    handleStatusChange,
  };
};
