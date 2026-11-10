import { useCallback, useEffect, useState } from 'react';
import { getContractorLoginAccess, type ContractorLoginAccess } from '@shared/api/contractors/getContractorLoginAccess';

export const useContractorLoginAccess = (contractors: ReadonlyArray<{ userId: string; status?: string }>) => {
  const key = JSON.stringify([...new Map(contractors.map((item) => [item.userId, [item.userId, item.status]])).values()].sort());
  const [states, setStates] = useState<Map<string, ContractorLoginAccess>>(new Map());
  const [loading, setLoading] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const ids = (JSON.parse(key) as [string, string][]).map(([id]) => id);
    const controller = new AbortController();
    setStates(new Map());
    setLoading(ids.length > 0);
    if (ids.length === 0) return () => controller.abort();
    const unknownStates = new Map(ids.map((id) => [id, {
      user_id: id, state: 'unknown' as const, label: 'Не удалось проверить',
      description: 'Не удалось подтвердить возможность входа. Повторите проверку позже.',
    }]));
    void getContractorLoginAccess(ids, controller.signal)
      .then((items) => {
        if (!controller.signal.aborted) setStates(new Map([
          ...unknownStates, ...items.filter((item) => unknownStates.has(item.user_id)).map((item) => [item.user_id, item] as const),
        ]));
      })
      .catch(() => { if (!controller.signal.aborted) setStates(unknownStates); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [key, attempt]);
  const refresh = useCallback(() => setAttempt((value) => value + 1), []);
  return { states, loading, refresh };
};
