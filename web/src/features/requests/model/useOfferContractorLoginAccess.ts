import { useContractorLoginAccess } from '@features/contractors/hooks/useContractorLoginAccess';
import type { RequestDetailsOffer } from '@shared/api/requests/getRequestDetails';

export const useOfferContractorLoginAccess = (offers: RequestDetailsOffer[]) =>
  useContractorLoginAccess(offers.flatMap((offer) =>
    offer.actions.view_contractor_info && offer.contractor_user_id
      ? [{ userId: offer.contractor_user_id }] : []));
