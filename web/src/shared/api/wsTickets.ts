import { fetchJson } from './client';

export type WsTicketPurpose = 'chat_ws' | 'realtime_ws' | 'notifications_ws';

type CreateWsTicketResponse = {
  ticket: string;
  expires_in: number;
  expires_at: string;
};

export const createWsTicket = async (purpose: WsTicketPurpose) => {
  return await fetchJson<CreateWsTicketResponse>(
    '/api/v1/ws/tickets',
    {
      method: 'POST',
      body: JSON.stringify({ purpose })
    },
    'Не удалось получить websocket ticket'
  );
};
