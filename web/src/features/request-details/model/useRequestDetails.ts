import { useLocation, useNavigate, useParams } from 'react-router-dom';
import type { RequestWithOfferStats } from '@shared/api/requests/getRequests';

export const useRequestDetails = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams<{ id: string }>();
  const requestFromLocation = (location.state as { request?: RequestWithOfferStats } | null)?.request;
  const requestId = Number(id ?? requestFromLocation?.id ?? 0);

  return {
    navigate,
    location,
    requestId,
    requestFromLocation
  };
};
