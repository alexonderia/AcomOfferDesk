import { fetchJson } from './client';

export type WsTicketPurpose = 'realtime_ws' | 'notifications_ws';

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
    'Не удалось получить билет websocket-подключения.'
  );
};
