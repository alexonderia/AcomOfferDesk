import { fetchJson } from '../client';
import { normalizeRecommendedHierarchyNode, type RecommendedHierarchyNode } from './types';

type ResponseShape = {
  data: {
    items: Array<Parameters<typeof normalizeRecommendedHierarchyNode>[0]>;
  };
};

export const getRecommendedUnitsTree = async (): Promise<RecommendedHierarchyNode[]> => {
  const response = await fetchJson<ResponseShape>(
    '/api/v1/units/recommended-tree',
    { method: 'GET' },
    'Не удалось загрузить рекомендуемую структуру'
  );

  return response.data.items.map(normalizeRecommendedHierarchyNode);
};
