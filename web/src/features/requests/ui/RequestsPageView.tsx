import { Box, Typography } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useRequestsPage } from '@features/requests/model/useRequestsPage';
import { RequestsTable } from '@features/requests/ui/RequestsTable';

export const RequestsPageView = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
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
  } = useRequestsPage();

  return (
    <Box>
      {errorMessage ? (
        <Typography color="error" sx={{ mb: 2 }}>
          {errorMessage}
        </Typography>
      ) : null}
      <RequestsTable
        requests={requests}
        isLoading={isLoading}
        onRowClick={(request) =>
          navigate(
            isContractor ? `/requests/${request.id}/contractor` : `/requests/${request.id}`,
            isContractor ? undefined : { state: { request } }
          )
        }
        chatAlertsMap={chatAlertsMap}
        ownerOptions={ownerOptions}
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
