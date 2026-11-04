import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { systemStatusFixture } from '@features/system-status/systemStatus.fixture';
import { useSystemStatus } from '@features/system-status/useSystemStatus';
import { appTheme } from '@shared/theme/appTheme';
import { SystemStatusPage } from './SystemStatusPage';

vi.mock('@features/system-status/useSystemStatus', () => ({ useSystemStatus: vi.fn() }));
const status = vi.mocked(useSystemStatus);
const reload = vi.fn();
const mount = () => render(<ThemeProvider theme={appTheme}><SystemStatusPage /></ThemeProvider>);

describe('system status panel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    status.mockReturnValue({ data: systemStatusFixture, error: null, loading: false, responseMs: 18, reload });
  });

  it('shows no-mail mode, service timings and current settings', () => {
    mount();
    expect(screen.getByRole('heading', { name: 'Состояние системы' })).toBeInTheDocument();
    expect(screen.getByText('Без почты (ограниченный)')).toBeInTheDocument();
    expect(within(screen.getByRole('article', { name: 'Ограниченный — без почты' })).getByText('Активен', { exact: true })).toBeInTheDocument();
    expect(within(screen.getByRole('article', { name: 'Полный — с почтой' })).getByText('Не активен', { exact: true })).toBeInTheDocument();
    expect(screen.getByText('С логином и начальным паролем')).toBeInTheDocument();
    expect(screen.getByText('2.4 мс')).toBeInTheDocument();
    expect(screen.getByText('18 мс')).toBeInTheDocument();
    expect(screen.getByText('Проверки пройдены')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Обновить' }));
    expect(reload).toHaveBeenCalledOnce();
  });

  it('shows degraded and disabled dependencies separately', () => {
    status.mockReturnValue({ data: {
      ...systemStatusFixture, overall: 'degraded', services: [
        { key: 'iam', name: 'IAM', status: 'down', response_ms: 3000, detail: 'Тайм-аут' },
        { key: 'guard', name: 'Файлы', status: 'disabled', response_ms: null, detail: 'Выключен' },
        { key: 'antivirus', name: 'Антивирус', status: 'degraded', response_ms: 4, detail: 'Не готов' },
      ],
    }, error: null, loading: false, responseMs: 3010, reload });
    mount();
    expect(screen.getByText('Есть замечания')).toBeInTheDocument();
    expect(screen.getByText('Недоступен')).toBeInTheDocument();
    expect(screen.getByText('Требует внимания')).toBeInTheDocument();
    expect(screen.getByText('Отключён')).toBeInTheDocument();
  });

  it('shows enabled mail as configuration without claiming delivery works', () => {
    status.mockReturnValue({ data: {
      ...systemStatusFixture,
      settings: { ...systemStatusFixture.settings, email_enabled: true, smtp_configured: true, imap_configured: true },
    }, error: null, loading: false, responseMs: 18, reload });
    mount();
    expect(screen.getByText('С почтой')).toBeInTheDocument();
    expect(within(screen.getByRole('article', { name: 'Полный — с почтой' })).getByText('Активен', { exact: true })).toBeInTheDocument();
    expect(within(screen.getByRole('article', { name: 'Ограниченный — без почты' })).getByText('Не активен', { exact: true })).toBeInTheDocument();
    expect(screen.getByText('С настройкой доступа по почте')).toBeInTheDocument();
    expect(screen.getByText(/доставка писем не проверяется/)).toBeInTheDocument();
  });

  it('marks retained data as stale after refresh error', () => {
    status.mockReturnValue({ data: systemStatusFixture, error: 'Нет связи', loading: false, responseMs: 18, reload });
    mount();
    expect(screen.getByText('Данные не обновлены')).toBeInTheDocument();
    expect(screen.getByText(/Показаны последние полученные данные/)).toBeInTheDocument();
    expect(screen.queryByText('Проверки пройдены')).not.toBeInTheDocument();
    expect(screen.getByText('Последний известный активный')).toBeInTheDocument();
    expect(screen.queryByText('Активен', { exact: true })).not.toBeInTheDocument();
  });

  it('does not claim availability before first successful load', () => {
    status.mockReturnValue({ data: null, error: null, loading: true, responseMs: null, reload });
    mount();
    expect(screen.getByRole('status')).toHaveTextContent('Проверяем доступность');
    expect(screen.getByRole('button', { name: 'Проверяем…' })).toBeDisabled();
    expect(screen.queryByText('Проверки пройдены')).not.toBeInTheDocument();
  });
});
