import { useEffect, useState } from 'react';
import { getManualContractorDuplicates, type ManualContractorDuplicate } from '@shared/api/users/getManualContractorDuplicates';

export const useManualContractorDuplicates = ({
  open, companyName = '', inn = '', companyMail = '', requestId,
}: {
  open: boolean;
  companyName?: string;
  inn?: string;
  companyMail?: string;
  requestId?: string;
}) => {
  const [duplicates, setDuplicates] = useState<ManualContractorDuplicate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const hasQuery = [companyName, inn, companyMail].some((value) => value.trim().length >= 2);

  useEffect(() => {
    let active = true;
    setDuplicates([]);
    setError(null);
    setLoading(open && hasQuery);
    if (!open || !hasQuery) return;
    const timer = window.setTimeout(() => {
      void getManualContractorDuplicates({ companyName, inn, companyMail, requestId })
        .then((items) => { if (active) setDuplicates(items); })
        .catch((reason: unknown) => {
          if (active) setError(reason instanceof Error ? reason.message : 'Не удалось проверить похожих контрагентов');
        })
        .finally(() => { if (active) setLoading(false); });
    }, 350);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [companyMail, companyName, hasQuery, inn, open, reloadKey, requestId]);

  return { duplicates, loading, error, hasQuery, reload: () => setReloadKey((value) => value + 1) };
};
