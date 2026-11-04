import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { appTheme } from '@shared/theme/appTheme';
import { ProfileButton } from './ProfileButton';

const mocks = vi.hoisted(() => ({ profile: vi.fn(), session: { roleId: 1, login: 'profile-user' } }));
vi.mock('@app/providers/AuthProvider', () => ({ useAuth: () => ({ session: mocks.session, logout: vi.fn() }) }));
vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({ showSuccessToast: vi.fn(), showSystemToast: vi.fn() }),
  useToastMessageEffect: vi.fn(),
}));
vi.mock('@shared/api/users/getCurrentUserProfile', () => ({
  getCurrentUserProfile: mocks.profile,
  getMyNotificationPreferences: vi.fn().mockResolvedValue({ emailAvailable: false, preferences: {} }),
  setMyUnavailabilityPeriod: vi.fn(),
  updateMyCompanyContacts: vi.fn(),
  updateMyNotificationPreferences: vi.fn(),
  updateMyProfile: vi.fn(),
}));

const profile = (roleId: number, canChange = true) => ({
  userId: 'profile-user', roleId, fullName: 'Profile user', phone: null, mail: null,
  company: {}, unavailablePeriod: null, unavailablePeriods: [],
  actions: { manage_credentials: canChange },
});

describe('password change inside the profile', () => {
  beforeEach(() => vi.clearAllMocks());

  it.each([1, 6])('renders the form in the single profile dialog for role %s', async (roleId) => {
    mocks.session.roleId = roleId;
    mocks.profile.mockResolvedValue(profile(roleId));
    render(<ThemeProvider theme={appTheme}><ProfileButton /></ThemeProvider>);
    expect(screen.queryByLabelText(/^Текущий пароль\s*\*?$/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Профиль' }));
    const form = await screen.findByRole('form', { name: 'Изменение пароля' });
    expect(screen.getAllByRole('dialog')).toHaveLength(1);
    expect(within(screen.getByRole('dialog')).getByRole('form', { name: 'Изменение пароля' })).toBe(form);
    expect(within(form).getByLabelText(/^Текущий пароль\s*\*?$/)).toBeVisible();
    expect(within(form).getByLabelText(/^Повтор нового пароля\s*\*?$/)).toBeVisible();
    expect(screen.queryByRole('button', { name: 'Изменить пароль' })).not.toBeInTheDocument();
    fireEvent.click(within(form).getByRole('button', { name: 'Показать текущий пароль' }));
    fireEvent.change(within(form).getByLabelText(/^Текущий пароль\s*\*?$/), { target: { value: 'private draft' } });
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });
    fireEvent.click(await screen.findByRole('button', { name: 'Профиль' }));
    expect(await screen.findByLabelText(/^Текущий пароль\s*\*?$/)).toHaveValue('');
    expect(screen.getByLabelText(/^Текущий пароль\s*\*?$/)).toHaveAttribute('type', 'password');
  });

  it('does not show credentials controls when the profile action is unavailable', async () => {
    mocks.profile.mockResolvedValue(profile(6, false));
    render(<ThemeProvider theme={appTheme}><ProfileButton /></ThemeProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'Профиль' }));
    await screen.findByText('Profile user');
    expect(screen.queryByRole('form', { name: 'Изменение пароля' })).not.toBeInTheDocument();
  });
});
