import { fetchJson } from '../client';

export type ContractorRootUnitBinding = {
  unitId: number;
  unitName: string;
  isBound: boolean;
  canManage: boolean;
};

export type ContractorRootUnitsResult = {
  contractorUserId: string;
  canManage: boolean;
  items: ContractorRootUnitBinding[];
};

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

export const getContractorRootUnits = async (contractorUserId: string): Promise<ContractorRootUnitsResult> => {
  const response = await fetchJson<ApiResponse>(
    `/api/v1/contractors/${encodeURIComponent(contractorUserId)}/root-units`,
    { method: 'GET' },
    'Не удалось загрузить привязки контрагента к подразделениям'
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
