import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useForm } from 'react-hook-form';
import { describe, expect, it, vi } from 'vitest';
import { appTheme } from '@shared/theme/appTheme';
import { PasswordTextField } from './PasswordTextField';
import { ValidatedTextField } from './ValidatedTextField';
import { InitialAccountFields } from '../InitialAccountFields';

describe('password visibility', () => {
  it('toggles each field independently without changing or submitting its value', () => {
    const submit = vi.fn((event) => event.preventDefault());
    render(<ThemeProvider theme={appTheme}><form onSubmit={submit}>
      <PasswordTextField label="Пароль" defaultValue="Password to inspect 123" autoComplete="new-password" />
      <PasswordTextField label="Подтверждение" defaultValue="Confirmation 123" />
    </form></ThemeProvider>);
    const input = screen.getByLabelText('Пароль');
    expect(input).toHaveAttribute('type', 'password');
    const toggle = screen.getByRole('button', { name: 'Показать пароль' });
    expect(toggle).toHaveAttribute('type', 'button');
    fireEvent.click(toggle);
    expect(input).toHaveAttribute('type', 'text');
    expect(input).toHaveValue('Password to inspect 123');
    expect(input).toHaveAttribute('autocomplete', 'new-password');
    expect(screen.getByLabelText('Подтверждение')).toHaveAttribute('type', 'password');
    expect(screen.getByRole('button', { name: 'Скрыть пароль' })).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(screen.getByRole('button', { name: 'Скрыть пароль' }));
    expect(input).toHaveAttribute('type', 'password');
    expect(submit).not.toHaveBeenCalled();
  });

  it('preserves existing adornments and disables the toggle with its input', () => {
    render(<ThemeProvider theme={appTheme}><PasswordTextField label="Пароль" disabled InputProps={{ endAdornment: <span>Suffix</span> }} /></ThemeProvider>);
    expect(screen.getByText('Suffix')).toBeVisible();
    expect(screen.getByRole('button', { name: 'Показать пароль' })).toBeDisabled();
    expect(screen.getByLabelText('Пароль')).toBeDisabled();
  });

  it('preserves react-hook-form registration through the validated field wrapper', async () => {
    const saved = vi.fn();
    const Form = () => {
      const { register, handleSubmit } = useForm({ defaultValues: { login: 'test-user', password: '' } });
      return <form onSubmit={handleSubmit((values) => saved(values))}>
        <ValidatedTextField label="Логин" registration={register('login')} />
        <ValidatedTextField label="Пароль" type="password" registration={register('password')} />
        <button type="submit">Сохранить</button>
      </form>;
    };
    render(<ThemeProvider theme={appTheme}><Form /></ThemeProvider>);
    fireEvent.change(screen.getByLabelText('Пароль'), { target: { value: 'Registered password 123' } });
    fireEvent.click(screen.getByRole('button', { name: 'Показать пароль' }));
    expect(saved).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }));
    await waitFor(() => expect(saved).toHaveBeenCalledWith({ login: 'test-user', password: 'Registered password 123' }));
  });

  it('covers both initial-password fields without changing the login field', () => {
    const change = vi.fn();
    render(<ThemeProvider theme={appTheme}><InitialAccountFields values={{ login: 'new-user', password: 'Password 123456', password_confirmation: 'Password 123456' }} onChange={change} /></ThemeProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'Показать начальный пароль' }));
    expect(screen.getByLabelText(/^Начальный пароль\s*\*?$/)).toHaveAttribute('type', 'text');
    expect(screen.getByLabelText(/^Повтор начального пароля\s*\*?$/)).toHaveAttribute('type', 'password');
    expect(screen.getByLabelText('Логин для входа', { exact: false })).toHaveAttribute('type', 'text');
    expect(change).not.toHaveBeenCalled();
  });
});
