import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Notification } from '../model/types';
import { NotificationItem } from './NotificationItem';
import { NotificationPushToast } from './NotificationPushToast';

vi.mock('./NotificationCard', () => ({
  NotificationCard: (props: Record<string, unknown>) => (
    <div
      data-testid="notification-card"
      data-variant={String(props.variant)}
      data-unread={String(props.isUnread)}
    />
  ),
}));

const notification: Notification = {
  id: 7,
  type: 'message.created',
  severity: 'info',
  title: 'Title',
  body: 'Body',
  entity_type: 'message',
  entity_id: 12,
  link_url: '/offers/12/workspace',
  payload: { offer_id: 12 },
  read_at: null,
  created_at: '2026-05-14T10:00:00Z',
};

describe('NotificationCard usage', () => {
  it('uses NotificationCard in center item variant', () => {
    render(<NotificationItem notification={notification} onClick={vi.fn()} />);

    const card = screen.getByTestId('notification-card');
    expect(card).toHaveAttribute('data-variant', 'center');
    expect(card).toHaveAttribute('data-unread', 'true');
  });

  it('uses NotificationCard in toast variant', () => {
    render(
      <NotificationPushToast
        notification={notification}
        onClick={vi.fn()}
        onClose={vi.fn()}
      />
    );

    const card = screen.getByTestId('notification-card');
    expect(card).toHaveAttribute('data-variant', 'toast');
    expect(card).toHaveAttribute('data-unread', 'true');
  });
});
