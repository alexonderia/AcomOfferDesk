import { Box } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useRef } from 'react';
import { useRequestsPage } from '@features/requests/model/useRequestsPage';
import { RequestsTable } from '@features/requests/ui/RequestsTable';
import { useSystemToasts } from '@shared/ui/toasts';

export const RequestsPageView = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showErrorToast, showSuccessToast } = useSystemToasts();
  const lastErrorRef = useRef<string | null>(null);
  const lastSuccessToastIdRef = useRef<number | null>(null);
  const {
    canCreateRequest,
    canEditOwner,
    chatAlertsMap,
    errorMessage,
    handleOwnerChange,
    isContractor,
    isLoading,
    ownerOptionsByRequestId,
    requests,
    successToastEvent,
    shouldLoadOpenRequests
  } = useRequestsPage();

  useEffect(() => {
    if (!errorMessage) {
      lastErrorRef.current = null;
      return;
    }
    if (lastErrorRef.current === errorMessage) {
      return;
    }
    showErrorToast(errorMessage);
    lastErrorRef.current = errorMessage;
  }, [errorMessage, showErrorToast]);

  useEffect(() => {
    if (!successToastEvent) {
      return;
    }
    if (lastSuccessToastIdRef.current === successToastEvent.id) {
      return;
    }
    showSuccessToast(successToastEvent.message);
    lastSuccessToastIdRef.current = successToastEvent.id;
  }, [showSuccessToast, successToastEvent]);

  return (
    <Box>
      <RequestsTable
        requests={requests}
        isLoading={isLoading}
        onRowClick={(request) =>
          navigate(
            isContractor
              ? `/requests/${request.id}/contractor?tab=${shouldLoadOpenRequests ? 'open' : 'my'}`
              : `/requests/${request.id}`,
            isContractor ? undefined : { state: { request } }
          )
        }
        chatAlertsMap={chatAlertsMap}
        ownerOptionsByRequestId={ownerOptionsByRequestId}
        canEditOwner={canEditOwner}
        onOwnerChange={(request, ownerUserId) => void handleOwnerChange(request, ownerUserId)}
        isContractor={isContractor}
        showContractorOffersColumn={isContractor && !shouldLoadOpenRequests}
        showContractorNotificationColumn={isContractor && !shouldLoadOpenRequests}
        onAddClick={
          canCreateRequest
            ? () => navigate('/requests/create', { state: { backgroundLocation: location } })
            : undefined
        }
      />
    </Box>
  );
};
