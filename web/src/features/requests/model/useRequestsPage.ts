import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { getOfferedRequests } from '@shared/api/requests/getOfferedRequests';
import { getOpenRequests } from '@shared/api/requests/getOpenRequests';
import { getRequestEconomists } from '@shared/api/requests/getRequestEconomists';
import { getRequests, type RequestWithOfferStats } from '@shared/api/requests/getRequests';
import { updateRequestDetails } from '@shared/api/requests/updateRequestDetails';
import { hasPermission } from '@shared/auth/permissions';
import { ROLE } from '@shared/constants/roles';
import { formatUnavailabilityDate, type UnavailabilityPeriodInfo } from '@shared/lib/unavailability';

const POLL_INTERVAL_MS = 10000;

const buildRequestsSignature = (items: RequestWithOfferStats[]) => JSON.stringify(
  items.map((item) => ({
    id: item.id,
    owner: item.id_user,
    status: item.status,
    updated_at: item.updated_at,
    deadline_at: item.deadline_at,
    id_offer: item.id_offer,
    unread_messages_count: item.unread_messages_count ?? 0,
    count_submitted: item.count_submitted ?? 0,
    count_deleted_alert: item.count_deleted_alert ?? 0,
    offers: (item.offers ?? []).map((offer) => ({
      id: offer.id,
      status: offer.status,
      unread_messages_count: offer.unread_messages_count ?? 0
    }))
  }))
);

const buildOwnerOptionsSignature = (
  items: Array<{ id: string; label: string; unavailablePeriod: UnavailabilityPeriodInfo | null }>
) => JSON.stringify(
  items.map((item) => ({
    id: item.id,
    label: item.label,
    unavailable: item.unavailablePeriod
      ? {
          status: item.unavailablePeriod.status,
          startedAt: item.unavailablePeriod.startedAt,
          endedAt: item.unavailablePeriod.endedAt
        }
      : null
  }))
);

export const useRequestsPage = () => {
  const { session } = useAuth();
  const [searchParams] = useSearchParams();
  const [requests, setRequests] = useState<RequestWithOfferStats[]>([]);
  const [ownerOptions, setOwnerOptions] = useState<Array<{ id: string; label: string; unavailablePeriod: UnavailabilityPeriodInfo | null }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [chatAlertsMap, setChatAlertsMap] = useState<Record<number, number>>({});
  const requestsSignatureRef = useRef('');
  const ownerOptionsSignatureRef = useRef('');

  const contractorTabParam = searchParams.get('tab');
  const contractorTab: 'my' | 'open' = contractorTabParam === 'open' ? 'open' : 'my';
  const isContractor = session?.roleId === ROLE.CONTRACTOR;

  const canLoadOpenRequests = useMemo(
    () => hasPermission(session, 'requests.open.read'),
    [session]
  );

  const canLoadMyRequests = useMemo(
    () => hasPermission(session, 'requests.offered.read'),
    [session]
  );

  const canUseContractorTabs = isContractor && canLoadOpenRequests && canLoadMyRequests;
  const shouldLoadOnlyOpenRequests = isContractor && !canUseContractorTabs && canLoadOpenRequests;
  const shouldLoadOpenRequests = shouldLoadOnlyOpenRequests || (canUseContractorTabs && contractorTab === 'open');

  const canEditOwner = useMemo(
    () => hasPermission(session, 'requests.owner.change'),
    [session]
  );
  const canCreateRequest = useMemo(
    () => hasPermission(session, 'requests.create'),
    [session]
  );

  const fetchRequests = useCallback(
    async (showLoading: boolean) => {
      if (showLoading) {
        setIsLoading(true);
      }
      setErrorMessage(null);

      try {
        const data = isContractor
          ? shouldLoadOpenRequests
            ? await getOpenRequests()
            : await getOfferedRequests()
          : await getRequests();

        const nextSignature = buildRequestsSignature(data.requests);
        if (requestsSignatureRef.current !== nextSignature) {
          requestsSignatureRef.current = nextSignature;
          setRequests(data.requests);
        }
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : 'Ошибка загрузки заявок');
      } finally {
        if (showLoading) {
          setIsLoading(false);
        }
      }
    },
    [isContractor, shouldLoadOpenRequests]
  );

  const fetchOwners = useCallback(async () => {
    if (!canEditOwner) {
      ownerOptionsSignatureRef.current = '';
      setOwnerOptions([]);
      return;
    }

    try {
      const economists = await getRequestEconomists();
      const nextOwnerOptions = economists.map((item) => ({
        id: item.user_id,
        label: `${item.full_name?.trim() || item.user_id} (${item.role})`,
        unavailablePeriod: item.unavailable_period
          ? {
              status: item.unavailable_period.status,
              startedAt: item.unavailable_period.started_at,
              endedAt: item.unavailable_period.ended_at,
            }
          : null,
      }));
      const nextSignature = buildOwnerOptionsSignature(nextOwnerOptions);
      if (ownerOptionsSignatureRef.current !== nextSignature) {
        ownerOptionsSignatureRef.current = nextSignature;
        setOwnerOptions(nextOwnerOptions);
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Ошибка загрузки списка ответственных');
    }
  }, [canEditOwner]);

  useEffect(() => {
    void fetchRequests(true);
    const intervalId = window.setInterval(() => {
      if (document.hidden) {
        return;
      }
      void fetchRequests(false);
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(intervalId);
  }, [fetchRequests]);

  useEffect(() => {
    void fetchOwners();
  }, [fetchOwners]);

  useEffect(() => {
    if (shouldLoadOpenRequests) {
      setChatAlertsMap({});
      return;
    }

    setChatAlertsMap(
      requests.reduce<Record<number, number>>((acc, request) => {
        const alertCount = request.count_chat_alert ?? 0;
        if (alertCount > 0) {
          acc[request.id] = alertCount;
        }
        return acc;
      }, {})
    );
  }, [requests, shouldLoadOpenRequests]);

  const handleOwnerChange = useCallback(
    async (request: RequestWithOfferStats, ownerUserId: string) => {
      if (!canEditOwner || !request.actions.change_owner || ownerUserId === request.id_user) {
        return;
      }

      const targetOwner = ownerOptions.find((item) => item.id === ownerUserId);
      if (targetOwner?.unavailablePeriod) {
        const start = formatUnavailabilityDate(targetOwner.unavailablePeriod.startedAt);
        const end = formatUnavailabilityDate(targetOwner.unavailablePeriod.endedAt);
        setErrorMessage(`Нельзя назначить ответственного: сотрудник в нерабочем статусе (${start} - ${end})`);
        return;
      }

      const previousOwner = request.id_user;
      setRequests((prev) =>
        prev.map((item) =>
          item.id === request.id
            ? {
                ...item,
                id_user: ownerUserId
              }
            : item
        )
      );

      try {
        await updateRequestDetails({
          requestId: request.id,
          owner_user_id: ownerUserId
        });
      } catch (error) {
        setRequests((prev) =>
          prev.map((item) =>
            item.id === request.id
              ? {
                  ...item,
                  id_user: previousOwner
                }
              : item
          )
        );
        setErrorMessage(error instanceof Error ? error.message : 'Не удалось изменить ответственного');
      }
    },
    [canEditOwner, ownerOptions]
  );

  return {
    canCreateRequest,
    canEditOwner,
    chatAlertsMap,
    errorMessage,
    handleOwnerChange,
    isContractor,
    isLoading,
    ownerOptions,
    requests,
    shouldLoadOpenRequests
  };
};
