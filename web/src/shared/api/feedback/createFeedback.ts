import { fetchJson } from '../client';

export type CreateFeedbackPayload = {
  text: string;
};

type CreateFeedbackResponse = {
  data: {
    feedback_id: number;
  };
};

export const createFeedback = async (payload: CreateFeedbackPayload): Promise<number> => {
  const response = await fetchJson<CreateFeedbackResponse>(
    '/api/v1/feedback',
    {
      method: 'POST',
      body: JSON.stringify(payload)
    },
    'Не удалось отправить обратную связь'
  );

  return response.data.feedback_id;
};
