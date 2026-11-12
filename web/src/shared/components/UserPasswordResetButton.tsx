import { Alert, Button, Dialog, DialogContent, DialogTitle, Stack, Typography } from '@mui/material';
import { useState } from 'react';
import { resetUserPassword } from '@shared/api/users/resetUserPassword';
import { useSystemToasts } from '@shared/ui/toasts';
import { PasswordTextField } from './forms/PasswordTextField';

type Props = { userId: string; canResetPassword?: boolean };

const ResetForm = ({ userId, onClose }: { userId: string; onClose: () => void }) => {
  const { showSuccessToast } = useSystemToasts();
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = async () => {
    if (busy) return;
    setError(null);
    if (password.length < 12 || password.length > 128 || password !== confirmation) {
      setError('Укажите совпадающий новый пароль длиной от 12 до 128 символов');
      return;
    }
    setBusy(true);
    try {
      await resetUserPassword(userId, { new_password: password, password_confirmation: confirmation });
      setPassword('');
      setConfirmation('');
      showSuccessToast(`Пароль пользователя ${userId} сброшен. Передайте ему новый пароль.`);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось сбросить пароль пользователя');
    } finally { setBusy(false); }
  };
  return (
    <Dialog open onClose={() => { if (!busy) onClose(); }} maxWidth="sm" fullWidth aria-labelledby="reset-user-password-title">
      <DialogTitle id="reset-user-password-title">Сброс пароля пользователя</DialogTitle>
      <DialogContent>
        <Stack component="form" spacing={2} sx={{ pt: 1 }} onSubmit={(e) => { e.preventDefault(); void submit(); }}>
          <Typography>Пользователь: {userId}</Typography>
          <Typography color="text.secondary">Задайте новый пароль без подтверждения старого. Пользователю потребуется войти заново. Письмо не отправляется, статус пользователя сохраняется.</Typography>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <PasswordTextField label="Новый пароль" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} inputProps={{ minLength: 12, maxLength: 128 }} helperText="От 12 до 128 символов" disabled={busy} required />
          <PasswordTextField label="Повтор нового пароля" autoComplete="new-password" value={confirmation} onChange={(e) => setConfirmation(e.target.value)} inputProps={{ maxLength: 128 }} disabled={busy} required />
          <Stack direction="row" justifyContent="flex-end" spacing={1}>
            <Button onClick={onClose} disabled={busy}>Отмена</Button>
            <Button type="submit" variant="contained" disabled={busy}>{busy ? 'Сохраняем…' : 'Установить новый пароль'}</Button>
          </Stack>
        </Stack>
      </DialogContent>
    </Dialog>
  );
};

export const UserPasswordResetButton = ({ userId, canResetPassword = false }: Props) => {
  const [open, setOpen] = useState(false);
  if (!canResetPassword) return null;
  return (
    <>
      <Button variant="outlined" onClick={() => setOpen(true)}>Сбросить пароль</Button>
      {open ? <ResetForm key={userId} userId={userId} onClose={() => setOpen(false)} /> : null}
    </>
  );
};
