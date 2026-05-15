import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { NotificationItem } from './NotificationItem';
import type { Notification } from '../model/types';

const notification: Notification = {
  id: 42,
  type: 'message.created',
  severity: 'info',
  title: 'New message',
  body: 'A new message was posted in the workspace chat.',
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

    expect(screen.getByText('New message')).toBeInTheDocument();
    expect(screen.getByText('A new message was posted in the workspace chat.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledWith(notification);
  });
});
