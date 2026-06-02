import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { appTheme } from '@shared/theme/appTheme';
import { ContractorInviteDialog } from './ContractorInviteDialog';

const inviteContractorsMock = vi.fn();
const getNormativeFilesMock = vi.fn();
const showErrorToastMock = vi.fn();
const showSuccessToastMock = vi.fn();

vi.mock('@shared/api/contractors/inviteContractors', () => ({
  inviteContractors: (...args: unknown[]) => inviteContractorsMock(...args),
}));

vi.mock('@shared/api/normative/getNormativeFiles', () => ({
  getNormativeFiles: (...args: unknown[]) => getNormativeFilesMock(...args),
}));

vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({
    showErrorToast: showErrorToastMock,
    showSuccessToast: showSuccessToastMock,
  }),
}));

const normativeItems = [
  {
    id: 42,
    file_id: 420,
    original_name: 'Презентация для поставщиков.pptx',
    status: 'actual' as const,
    created_at: '2026-06-01T00:00:00Z',
    download_url: '/api/v1/files/420/download',
  },
  {
    id: 43,
    file_id: 430,
    original_name: 'Общий регламент.pdf',
    status: 'actual' as const,
    created_at: '2026-06-01T00:00:00Z',
    download_url: '/api/v1/files/430/download',
  },
];

describe('ContractorInviteDialog', () => {
  beforeEach(() => {
    inviteContractorsMock.mockReset();
    getNormativeFilesMock.mockReset();
    showErrorToastMock.mockReset();
    showSuccessToastMock.mockReset();
    getNormativeFilesMock.mockResolvedValue(normativeItems);
  });

  it('adds emails through shared additional-emails input and sends invite', async () => {
    inviteContractorsMock.mockResolvedValue({
      data: {
        sent: ['valid1@example.com', 'valid2@example.com'],
        failed: [],
        invalid: [],
      },
    });

    render(
      <ThemeProvider theme={appTheme}>
        <ContractorInviteDialog open onClose={vi.fn()} />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(getNormativeFilesMock).toHaveBeenCalledWith('actual');
    });

    expect(screen.getByText('Пример письма')).toBeInTheDocument();
    expect(screen.getByText('Тема: Приглашение в AcomOfferDesk')).toBeInTheDocument();

    const preview = screen.getByText((_, element) => element?.tagName === 'PRE');
    expect(preview).toHaveTextContent('<!DOCTYPE html>');
    expect(preview).toHaveTextContent('<html lang="ru">');
    expect(preview).toHaveTextContent('<a href="{{PORTAL_URL}}"');
    expect(preview).toHaveTextContent('{{CONTACT_EMAIL}}');

    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'valid1@example.com, valid2@example.com' },
    });
    fireEvent.click(screen.getByLabelText('Добавить email'));
    fireEvent.click(screen.getByRole('button', { name: 'Отправить' }));

    await waitFor(() => {
      expect(inviteContractorsMock).toHaveBeenCalledWith({
        emails: ['valid1@example.com', 'valid2@example.com'],
        normativeFileId: 42,
      });
    });
    expect(showSuccessToastMock).toHaveBeenCalled();
  });

  it('shows loading while invite request is pending', async () => {
    inviteContractorsMock.mockImplementation(() => new Promise(() => {}));

    render(
      <ThemeProvider theme={appTheme}>
        <ContractorInviteDialog open onClose={vi.fn()} />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(getNormativeFilesMock).toHaveBeenCalledWith('actual');
    });

    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'valid@example.com' },
    });
    fireEvent.click(screen.getByLabelText('Добавить email'));
    fireEvent.click(screen.getByRole('button', { name: 'Отправить' }));

    expect(screen.getByRole('button', { name: 'Отправка...' })).toBeDisabled();
  });

  it('shows backend failure details', async () => {
    inviteContractorsMock.mockResolvedValue({
      data: {
        sent: [],
        failed: [{ email: 'valid@example.com', reason: 'queue failed' }],
        invalid: [],
      },
    });

    render(
      <ThemeProvider theme={appTheme}>
        <ContractorInviteDialog open onClose={vi.fn()} />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(getNormativeFilesMock).toHaveBeenCalledWith('actual');
    });

    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'valid@example.com' },
    });
    fireEvent.click(screen.getByLabelText('Добавить email'));
    fireEvent.click(screen.getByRole('button', { name: 'Отправить' }));

    await waitFor(() => {
      expect(screen.getByText(/Отправлено: 0/)).toBeInTheDocument();
      expect(screen.getByText('valid@example.com: queue failed')).toBeInTheDocument();
    });
    expect(showErrorToastMock).toHaveBeenCalled();
  });

  it('shows inline validation for invalid email token', async () => {
    render(
      <ThemeProvider theme={appTheme}>
        <ContractorInviteDialog open onClose={vi.fn()} />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(getNormativeFilesMock).toHaveBeenCalledWith('actual');
    });

    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'bad-email' },
    });
    fireEvent.click(screen.getByLabelText('Добавить email'));

    expect(screen.getByText('Некорректный email: bad-email')).toBeInTheDocument();
  });
});
