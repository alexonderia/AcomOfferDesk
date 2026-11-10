import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { ContractorLoginAccess } from '@shared/api/contractors/getContractorLoginAccess';
import { ContractorChatAccessNotice } from './ContractorChatAccessNotice';

const access = (state: ContractorLoginAccess['state']): ContractorLoginAccess => ({
  user_id: 'contractor-1', state, label: state === 'password_not_set' ? 'Пароль не задан' : 'Вход отключён', description: '',
});

describe('ContractorChatAccessNotice', () => {
  it.each(['not_granted', 'blocked', 'pending', 'password_not_set', 'temporarily_locked'] as const)('warns in a tooltip when entry is unavailable: %s', async (state) => {
    render(<ContractorChatAccessNotice access={access(state)} />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    fireEvent.mouseOver(screen.getByRole('button', { name: 'У контрагента нет доступа к системе' }));
    expect(await screen.findByRole('tooltip')).toHaveTextContent('Контрагент не может войти в систему');
    expect(screen.getByRole('tooltip')).toHaveTextContent('прочитать новые сообщения в личном кабинете');
  });
  it.each(['available', 'setup_required'] as const)('does not claim a lack of access for %s', (state) => {
    render(<ContractorChatAccessNotice access={access(state)} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
  it('distinguishes failed checks without offering a check button in chat', async () => {
    render(<ContractorChatAccessNotice access={access('unknown')} />);
    fireEvent.mouseOver(screen.getByRole('button', { name: 'Не удалось проверить доступ контрагента' }));
    expect(await screen.findByRole('tooltip')).toHaveTextContent('Не удалось проверить');
    expect(screen.getByRole('tooltip')).not.toHaveTextContent('не может войти');
    expect(screen.queryByRole('button', { name: /Проверить/ })).not.toBeInTheDocument();
  });
  it('does not display an old warning while rechecking', () => {
    render(<ContractorChatAccessNotice access={access('blocked')} loading />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
