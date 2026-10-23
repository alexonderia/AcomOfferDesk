import { createFilterOptions } from '@mui/material/Autocomplete';
import type { RequestContractorItem } from '@shared/api/users/getRequestContractors';

export const contractorSearchText = (contractor: RequestContractorItem): string =>
  [
    contractor.company_name,
    contractor.full_name,
    contractor.company_mail,
    contractor.mail,
    contractor.user_id
  ]
    .filter((value): value is string => Boolean(value && value.trim()))
    .join(' ');

export const filterManualOfferContractors = createFilterOptions<RequestContractorItem>({
  stringify: contractorSearchText,
  trim: true,
  ignoreCase: true
});
