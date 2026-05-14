import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { NotificationItem } from './NotificationItem';
import type { Notification } from '../model/types';

const notification: Notification = {
  id: 42,
  type: 'message.created',
  severity: 'info',
  title: 'Новое сообщение',
  body: 'В чате по заявке появилось новое сообщение.',
  entity_type: 'message',
  entity_id: 21,
  link_url: '/offers/21/workspace',
  payload: { request_id: 10 },
  read_at: null,
  created_at: '2026-05-14T10:00:00Z',
};

describe('NotificationItem', () => {
  it('renders notification content and handles click', () => {
    const handleClick = vi.fn();

    render(<NotificationItem notification={notification} onClick={handleClick} />);

    expect(screen.getByText('Новое сообщение')).toBeInTheDocument();
    expect(screen.getByText('В чате по заявке появилось новое сообщение.')).toBeInTheDocument();
    expect(screen.getByText('info')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledWith(notification);
  });
});
