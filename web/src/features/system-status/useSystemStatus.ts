import { useEffect, useState } from 'react';
import { getSystemStatus, type SystemStatus } from '@shared/api/system/getSystemStatus';

export const useSystemStatus = () => {
  const [data, setData] = useState<SystemStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [responseMs, setResponseMs] = useState<number | null>(null);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    let inFlight = false;
    const load = async () => {
      if (inFlight) return;
      inFlight = true;
      setLoading(true);
      const started = performance.now();
      try {
        const result = await getSystemStatus(controller.signal);
        if (active) {
          setData(result);
          setResponseMs(Math.round(performance.now() - started));
          setError(null);
        }
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : 'Не удалось получить состояние системы');
      } finally {
        inFlight = false;
        if (active) setLoading(false);
      }
    };
    const refreshVisible = () => { if (!document.hidden) void load(); };
    void load();
    const timer = window.setInterval(refreshVisible, 30_000);
    document.addEventListener('visibilitychange', refreshVisible);
    return () => {
      active = false;
      controller.abort();
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', refreshVisible);
    };
  }, [revision]);

  return { data, error, loading, responseMs, reload: () => setRevision((value) => value + 1) };
};
