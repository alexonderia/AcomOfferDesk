import { fetchJson } from '../client';

export type FeedbackListItem = {
  id: number;
  text: string;
  author_user_id?: string | null;
  author_name?: string | null;
  created_at?: string | null;
};

type FeedbackListResponse = {
  data: {
    items: FeedbackListItem[];
    total: number;
    limit: number;
    offset: number;
  };
};

export const getFeedbackList = async (): Promise<FeedbackListItem[]> => {
  const response = await fetchJson<FeedbackListResponse>(
    '/api/v1/feedback',
    { method: 'GET' },
    'Не удалось загрузить обратную связь'
  );

  return response.data.items;
};

export const getFeedbackPage = async (query: { search: string; author: string; sortBy: string; sortOrder: string; page: number; pageSize: number }) => {
  const params = new URLSearchParams({ search: query.search, sort_by: query.sortBy, sort_order: query.sortOrder, limit: String(query.pageSize), offset: String(query.page * query.pageSize) });
  if (query.author.trim()) params.set('author_user_id', query.author.trim());
  return (await fetchJson<FeedbackListResponse>(`/api/v1/feedback?${params}`, { method: 'GET' }, 'Не удалось загрузить обратную связь')).data;
};
