import { fetchEmpty } from '../client';

export const deleteUnit = async (unitId: number, confirmReassign = false): Promise<void> => {
  const query = confirmReassign ? '?confirm_reassign=true' : '';
  await fetchEmpty(
    `/api/v1/units/${unitId}${query}`,
    { method: 'DELETE' },
    'Не удалось удалить юнит'
  );
};
