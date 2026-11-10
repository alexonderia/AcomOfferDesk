import { fireEvent, render as renderTesting, screen, waitFor, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { appTheme } from '@shared/theme/appTheme';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { UnitMember } from '@shared/api/units';
import { HierarchyProfileProvider } from './HierarchyProfileProvider';
import { PeopleFlatList, PeopleTree } from './PeopleTree';
import { UnitOrgReadonlyList } from './UnitOrgReadonlyList';

const mocks = vi.hoisted(() => ({ profile: vi.fn(), hierarchy: vi.fn(), units: vi.fn(), auth: vi.fn() }));
const render = (ui: ReactNode) => renderTesting(<ThemeProvider theme={appTheme}>{ui}</ThemeProvider>);
vi.mock('@app/providers/AuthProvider', () => ({ useAuth: mocks.auth }));
vi.mock('@shared/api/users/getEmployeeProfile', () => ({ getEmployeeProfile: mocks.profile }));
vi.mock('@shared/api/users/getUserHierarchy', () => ({ getUserHierarchy: mocks.hierarchy }));
vi.mock('@shared/api/users/getUserHierarchyUnitsTree', () => ({ getUserHierarchyUnitsTree: mocks.units }));

const member: UnitMember = { user_id: 'econ-1', full_name: 'Иванов Иван Иванович', role_id: 6, role_name: 'Экономист', status: 'active', id_parent_user: null };
const profile = { user_id: member.user_id, role_id: 6, full_name: member.full_name, phone: '+79991234567', mail: 'ivan@example.test', status: 'active' };
const manager: UnitMember = { ...member, user_id: 'lead-1', full_name: 'Петров Пётр Петрович', role_id: 5, role_name: 'Ведущий экономист' };
const hierarchy = {
  user: { userId: member.user_id, fullName: member.full_name, roleId: member.role_id, roleName: member.role_name, status: member.status },
  units: [{ unitId: 1, name: 'Отдел', parentUnitId: null }],
  managers: [{ userId: manager.user_id, fullName: manager.full_name, roleId: manager.role_id, roleName: manager.role_name,
    status: 'active', sourceUnitId: 1, sourceUnitName: 'Отдел' }],
  subordinates: [],
  legacyHierarchy: { legacyManager: null, legacySubordinates: [], isBusinessSource: false, note: '' },
};
const units = [{ unit_id: 1, id_parent: null, name: 'Отдел', is_active: true, members: [manager, { ...member, id_parent_user: manager.user_id }],
  children: [], actions: { canCreateChild: false, canUpdate: false, canDelete: false, canManageMembers: false } }];
const open = () => fireEvent.click(screen.getByRole('button', { name: `Открыть карточку сотрудника ${member.full_name}` }));
const renderList = (extra = {}) => render(<HierarchyProfileProvider><PeopleFlatList title="Сотрудники" emptyLabel="Нет" members={[member]} {...extra} /></HierarchyProfileProvider>);

describe('hierarchy employee profiles', () => {
  beforeEach(() => {
    mocks.auth.mockReturnValue({ session: { permissions: ['units.read', 'users.read'] } });
    mocks.profile.mockReset();
    mocks.profile.mockResolvedValue(profile);
    mocks.hierarchy.mockReset();
    mocks.hierarchy.mockResolvedValue(hierarchy);
    mocks.units.mockReset();
    mocks.units.mockResolvedValue(units);
  });

  it('loads only on click, displays contact details and closes without leaving hierarchy', async () => {
    renderList();
    expect(mocks.profile).not.toHaveBeenCalled();
    open();
    expect(await screen.findByText('ivan@example.test')).toBeVisible();
    expect(screen.getByRole('dialog', { name: 'Карточка сотрудника' })).toBeVisible();
    expect(screen.getByText('Иерархия по объединениям')).toBeVisible();
    expect(await screen.findByText('Отдел')).toBeVisible();
    expect(screen.getByText('+7 (999) 123-45-67')).toBeVisible();
    expect(mocks.profile).toHaveBeenCalledWith('econ-1', expect.any(AbortSignal));
    expect(mocks.hierarchy).toHaveBeenCalledWith('econ-1', expect.any(AbortSignal));
    expect(mocks.units).toHaveBeenCalledWith('econ-1', expect.any(AbortSignal));
    fireEvent.click(screen.getByRole('button', { name: 'Закрыть' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(screen.getByRole('button', { name: `Открыть карточку сотрудника ${member.full_name}` })).toBeVisible();
  });

  it('supports the nested readonly hierarchy', async () => {
    render(<HierarchyProfileProvider><UnitOrgReadonlyList units={[{
      unit_id: 1, id_parent: null, name: 'Корень', is_active: true, members: [],
      actions: { canCreateChild: false, canUpdate: false, canDelete: false, canManageMembers: false },
      children: [{ unit_id: 2, id_parent: 1, name: 'Ветка', is_active: true, members: [member], children: [], actions: { canCreateChild: false, canUpdate: false, canDelete: false, canManageMembers: false } }],
    }]} /></HierarchyProfileProvider>);
    open();
    expect(await screen.findByText('ivan@example.test')).toBeVisible();
  });

  it('keeps move and removal actions separate from profile opening', async () => {
    const move = vi.fn();
    const remove = vi.fn();
    render(<HierarchyProfileProvider><PeopleTree title="Состав" emptyLabel="Нет" members={[member]} onMove={move} onRemove={remove} /></HierarchyProfileProvider>);
    fireEvent.click(screen.getByRole('button', { name: `Переместить ${member.full_name}` }));
    expect(move).toHaveBeenCalledWith(expect.objectContaining(member));
    expect(mocks.profile).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: `Открепить ${member.full_name}` }));
    expect(remove).toHaveBeenCalledWith(expect.objectContaining(member));
    expect(mocks.profile).not.toHaveBeenCalled();
    open();
    expect(await screen.findByText('ivan@example.test')).toBeVisible();
  });

  it('shows server access errors and allows retry', async () => {
    mocks.profile.mockRejectedValueOnce(new Error('Недостаточно прав для просмотра профиля сотрудника'));
    renderList();
    open();
    expect(await screen.findByRole('alert')).toHaveTextContent('Недостаточно прав');
    expect(screen.queryByText('ivan@example.test')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Повторить' }));
    expect(await screen.findByText('ivan@example.test')).toBeVisible();
  });

  it('aborts loading on close and never displays a late response for another employee', async () => {
    let finish!: (value: typeof profile) => void;
    mocks.profile.mockReturnValueOnce(new Promise((resolve) => { finish = resolve; }));
    renderList();
    open();
    const signal = mocks.profile.mock.calls[0]![1] as AbortSignal;
    expect(mocks.hierarchy.mock.calls[0]![1]).toBe(signal);
    expect(mocks.units.mock.calls[0]![1]).toBe(signal);
    fireEvent.click(screen.getByRole('button', { name: 'Закрыть' }));
    await waitFor(() => expect(signal.aborted).toBe(true));
    finish({ ...profile, mail: 'stale@example.test' });
    open();
    expect(await screen.findByText('ivan@example.test')).toBeVisible();
    expect(screen.queryByText('stale@example.test')).not.toBeInTheDocument();
  });

  it('does not offer contact profiles without users.read', () => {
    mocks.auth.mockReturnValue({ session: { permissions: ['units.read'] } });
    renderList();
    expect(screen.queryByRole('button', { name: /Открыть карточку сотрудника/ })).not.toBeInTheDocument();
  });

  it('switches employees inside the card without stacking a separate profile dialog', async () => {
    renderList();
    open();
    expect(await screen.findByText('ivan@example.test')).toBeVisible();
    const card = screen.getByRole('dialog', { name: 'Карточка сотрудника' });
    mocks.profile.mockResolvedValueOnce({ ...profile, user_id: manager.user_id, full_name: manager.full_name, mail: 'petr@example.test' });
    mocks.hierarchy.mockResolvedValueOnce({ ...hierarchy, user: hierarchy.managers[0] });

    fireEvent.click(await within(card).findByRole('button', { name: `Открыть карточку сотрудника ${manager.full_name}` }));

    expect(await screen.findByText('petr@example.test')).toBeVisible();
    expect(screen.queryByText('ivan@example.test')).not.toBeInTheDocument();
    expect(screen.getAllByRole('dialog')).toHaveLength(1);
    expect(screen.getByRole('dialog', { name: 'Карточка сотрудника' })).toBeVisible();
  });

  it('shows a hierarchy loading error inside the employee card and can retry', async () => {
    mocks.hierarchy.mockRejectedValueOnce(new Error('Не удалось загрузить иерархию сотрудника'));
    renderList();
    open();
    expect(await screen.findByText('ivan@example.test')).toBeVisible();
    expect(await screen.findByRole('alert')).toHaveTextContent('Не удалось загрузить иерархию');
    fireEvent.click(screen.getByRole('button', { name: 'Повторить' }));
    expect(await screen.findByText('Отдел')).toBeVisible();
  });
});
