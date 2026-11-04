import { Alert, Button, Stack, Typography } from '@mui/material';
import { useState } from 'react';
import { useAuth } from '@app/providers/AuthProvider';
import { changePassword } from '@shared/api/auth/changePassword';
import { useSystemToasts } from '@shared/ui/toasts';
import { PasswordTextField } from './forms/PasswordTextField';

export const PasswordChangeForm = () => {
  const { logout } = useAuth();
  const { showSuccessToast } = useSystemToasts();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const clear = () => {
    if (busy) return;
    setCurrent('');
    setNext('');
    setConfirmation('');
    setError(null);
  };
  const submit = async () => {
    setError(null);
    if (!current || next.length < 12 || next.length > 128 || next !== confirmation) {
      setError('Укажите текущий пароль и совпадающий новый пароль длиной от 12 до 128 символов');
      return;
    }
    setBusy(true);
    try {
      await changePassword({ current_password: current, new_password: next, password_confirmation: confirmation });
      setCurrent('');
      setNext('');
      setConfirmation('');
      showSuccessToast('Пароль изменён. Войдите с новым паролем.');
      logout();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось изменить пароль');
    } finally {
      setBusy(false);
    }
  };
  return (
    <Stack component="form" aria-label="Изменение пароля" spacing={2} onSubmit={(e) => { e.preventDefault(); void submit(); }}>
      <Typography component="h3" variant="h5" fontWeight={600}>Изменение пароля</Typography>
      <Typography color="text.secondary">Подтвердите текущий пароль. После сохранения потребуется повторный вход.</Typography>
      {error ? <Alert severity="error">{error}</Alert> : null}
      <PasswordTextField label="Текущий пароль" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} inputProps={{ maxLength: 128 }} disabled={busy} required />
      <PasswordTextField label="Новый пароль" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} inputProps={{ minLength: 12, maxLength: 128 }} helperText="От 12 до 128 символов" disabled={busy} required />
      <PasswordTextField label="Повтор нового пароля" autoComplete="new-password" value={confirmation} onChange={(e) => setConfirmation(e.target.value)} inputProps={{ maxLength: 128 }} disabled={busy} required />
      <Stack direction="row" spacing={1} justifyContent="flex-end">
        <Button onClick={clear} disabled={busy}>Очистить</Button>
        <Button type="submit" variant="contained" disabled={busy}>{busy ? 'Сохраняем…' : 'Сохранить пароль'}</Button>
      </Stack>
    </Stack>
  );
};
