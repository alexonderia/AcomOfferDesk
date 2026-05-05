import type { OfferContractorInfo } from '@shared/api/offers/getOfferContractorInfo';
import type { OfferWorkspace } from '@shared/api/offers/getOfferWorkspace';
import type { OfferWorkspaceMessage } from '@shared/api/offers/offerWorkspaceActions';

export type OfferWorkspaceState = {
  workspace: OfferWorkspace | null;
  contractorInfo: OfferContractorInfo | null;
  selectedOfferId: number;
  errorMessage: string | null;
  isLoading: boolean;
};

export type OfferMessagesState = {
  messages: OfferWorkspaceMessage[];
  isSending: boolean;
  chatErrorMessage: string | null;
};
