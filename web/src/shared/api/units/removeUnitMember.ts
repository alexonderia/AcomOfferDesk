import { fetchEmpty } from '../client';

export const removeUnitMember = async (unitId: number, userId: string): Promise<void> => {
  await fetchEmpty(
    `/api/v1/units/${unitId}/members/${encodeURIComponent(userId)}`,
    { method: 'DELETE' },
    'Не удалось удалить участника'
  );
};
