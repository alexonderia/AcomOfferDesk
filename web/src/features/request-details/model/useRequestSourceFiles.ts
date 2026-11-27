import { useEffect, useState } from 'react';
import { fetchJson } from '@shared/api/client';
import type { RequestDetailsFile } from '@shared/api/requests/getRequestDetails';

type RequestHiddenFile = RequestDetailsFile & { is_specification_source: boolean | null; can_delete?: boolean };

export const useRequestSourceFiles = (requestId: string, refreshRevision = 0) => {
  const [state, setState] = useState<{ files: RequestHiddenFile[]; loading: boolean; error: string | null }>({
    files: [], loading: true, error: null,
  });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setState({ files: [], loading: true, error: null });
    fetchJson<{ files: RequestHiddenFile[] }>(`/api/v1/requests/${encodeURIComponent(requestId)}/source-files`,
      { method: 'GET', signal: controller.signal }, 'Не удалось загрузить исходники заявки')
      .then((result) => { if (!controller.signal.aborted) setState({ files: result.files, loading: false, error: null }); })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setState({ files: [], loading: false,
          error: error instanceof Error ? error.message : 'Не удалось загрузить исходники заявки' });
      });
    return () => controller.abort();
  }, [requestId, revision, refreshRevision]);
  return { ...state, retry: () => setRevision((value) => value + 1) };
};
