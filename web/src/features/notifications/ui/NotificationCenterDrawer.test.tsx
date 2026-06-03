import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { appTheme } from '@shared/theme/appTheme';
import { NotificationCenterDrawer } from './NotificationCenterDrawer';

vi.mock('./useNotificationCenterSize', () => ({
  useNotificationCenterSize: () => ({
    size: { width: 420, height: 520 },
    resizeHandleProps: {
      onPointerDown: vi.fn(),
      onPointerMove: vi.fn(),
      onPointerUp: vi.fn(),
      onPointerCancel: vi.fn(),
      onDoubleClick: vi.fn()
    }
  })
}));

describe('NotificationCenterDrawer', () => {
  it('renders the mobile notification center as a fullscreen centered layer without resize handle', () => {
    render(
      <ThemeProvider theme={appTheme}>
        <NotificationCenterDrawer
          anchorCorner={null}
          open
          notifications={[]}
          hasUnread={false}
          isLoading={false}
          isMarkAllPending={false}
          error={null}
          markingIds={new Set()}
          onClose={() => undefined}
          onRetry={() => undefined}
          onMarkAll={() => undefined}
          onNotificationClick={() => undefined}
        />
      </ThemeProvider>
    );

    expect(screen.getByRole('dialog', { name: 'Уведомления' })).toBeInTheDocument();
    expect(screen.queryByRole('separator')).not.toBeInTheDocument();
  });
});
