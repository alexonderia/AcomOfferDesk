import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';
import { ThemeProvider } from '@mui/material';
import { appTheme } from '@shared/theme/appTheme';
import { ROLE } from '@shared/constants/roles';
import { roleGuides } from '@shared/content/roleGuides';
import { RoleGuideButton, RoleGuideDialog } from './RoleGuideButton';

let roleId: number = ROLE.CONTRACTOR;
vi.mock('@app/providers/AuthProvider', () => ({ useAuth: () => ({ session: { roleId } }) }));
const wrapper = ({ children }: { children: ReactNode }) => <ThemeProvider theme={appTheme}>{children}</ThemeProvider>;

describe('Role guide reader', () => {
  beforeEach(() => { roleId = ROLE.CONTRACTOR; });

  it('opens only the current role guide and exposes chapter navigation', () => {
    render(<RoleGuideButton />, { wrapper });
    fireEvent.click(screen.getByRole('button', { name: 'Открыть памятку по роли' }));
    const dialog = screen.getByRole('dialog', { name: 'Руководство контрагента' });
    expect(within(dialog).getByRole('navigation', { name: 'Оглавление руководства' })).toBeInTheDocument();
    expect(within(dialog).queryByRole('button', { name: /Иерархия|различия ролей/ })).not.toBeInTheDocument();
    expect(within(dialog).getByText('Документация и инструкции', { exact: true })).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Мои заявки и статусы моих КП' }));
    expect(within(dialog).getByRole('heading', { level: 2, name: 'Мои заявки и статусы моих КП' })).toBeInTheDocument();
    expect(within(dialog).getByRole('article')).toHaveFocus();
  });

  it('does not reveal employee documentation through search and supports clearing a failed search', () => {
    render(<RoleGuideDialog guide={roleGuides[ROLE.CONTRACTOR]} open onClose={vi.fn()} />, { wrapper });
    fireEvent.change(screen.getByRole('textbox', { name: 'Поиск по руководству' }), { target: { value: 'иерархия' } });
    expect(screen.getByText('Ничего не найдено')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Иерархия:/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Очистить поиск' }));
    expect(screen.getByRole('heading', { level: 2, name: 'Начало работы' })).toBeInTheDocument();
  });

  it('shows all comparison columns for staff and closes with the accessible control or Escape', () => {
    const onClose = vi.fn();
    render(<RoleGuideDialog guide={roleGuides[ROLE.PROJECT_MANAGER]} open onClose={onClose} />, { wrapper });
    fireEvent.click(screen.getByRole('button', { name: 'Руководитель проекта, ведущий экономист и экономист: различия ролей' }));
    for (const name of ['Руководитель проекта', 'Ведущий экономист', 'Экономист']) {
      expect(screen.getByRole('columnheader', { name })).toBeInTheDocument();
    }
    fireEvent.click(screen.getByRole('button', { name: 'Закрыть руководство' }));
    expect(onClose).toHaveBeenCalledTimes(1);
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape', code: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it('hides the trigger for an unknown role', () => {
    roleId = 999;
    render(<RoleGuideButton />, { wrapper });
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
