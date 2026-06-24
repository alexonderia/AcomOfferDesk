import { fetchJson } from '../client';
import type { ContractorRootUnitsResult } from './getContractorRootUnits';

type ApiResponse = {
  data: {
    contractor_user_id: string;
    can_manage?: boolean;
    items?: Array<{
      unit_id: number;
      unit_name: string;
      is_bound: boolean;
      can_manage?: boolean;
    }>;
  };
};

export const updateContractorRootUnits = async (
  contractorUserId: string,
  rootUnitIds: number[],
): Promise<ContractorRootUnitsResult> => {
  const response = await fetchJson<ApiResponse>(
    `/api/v1/contractors/${encodeURIComponent(contractorUserId)}/root-units`,
    {
      method: 'PUT',
      body: JSON.stringify({ root_unit_ids: rootUnitIds }),
    },
    'Не удалось сохранить привязки контрагента к подразделениям'
  );

  return {
    contractorUserId: response.data.contractor_user_id,
    canManage: Boolean(response.data.can_manage),
    items: (response.data.items ?? []).map((item) => ({
      unitId: item.unit_id,
      unitName: item.unit_name,
      isBound: Boolean(item.is_bound),
      canManage: Boolean(item.can_manage),
    })),
  };
};
