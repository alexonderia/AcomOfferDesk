import { fetchJson } from '../client';

export type FeedbackListItem = {
  id: number;
  text: string;
};

type FeedbackListResponse = {
  data: {
    items: FeedbackListItem[];
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
