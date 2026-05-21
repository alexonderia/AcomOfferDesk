export type NotificationSeverity = 'info' | 'success' | 'warning' | 'error';

export type Notification = {
  id: number;
  type: string;
  severity: NotificationSeverity;
  title: string;
  body: string;
  entity_type: string | null;
  entity_id: number | null;
  link_url: string | null;
  payload: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
};

export type UnreadCount = {
  count: number;
};

export type NotificationQueryParams = {
  limit?: number;
  offset?: number;
};

