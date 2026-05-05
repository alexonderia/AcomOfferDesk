import { fetchJson } from '../client';

type DeletePlanResponse = {
  data: {
    deleted_plan_id: number;
  };
};

export const deletePlan = async (planId: number): Promise<number> => {
  const response = await fetchJson<DeletePlanResponse>(
    `/api/v1/plans/${planId}`,
    {
      method: 'DELETE',
    },
    'Не удалось удалить дочерний план'
  );
  return response.data.deleted_plan_id;
};
