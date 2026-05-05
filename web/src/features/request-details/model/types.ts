import type { RequestDetails } from '@shared/api/requests/getRequestDetails';

export type RequestDetailsState = {
  requestDetails: RequestDetails | null;
  errorMessage: string | null;
  successMessage: string | null;
};
