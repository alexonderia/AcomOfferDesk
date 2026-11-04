import { Stack, TextField, Typography } from '@mui/material';
import { PasswordTextField } from './forms/PasswordTextField';

export type InitialAccountValues = { login: string; password: string; password_confirmation: string };

export const InitialAccountFields = ({ values, onChange, disabled = false }: {
  values: InitialAccountValues;
  onChange: (field: keyof InitialAccountValues, value: string) => void;
  disabled?: boolean;
}) => {
  const required = Boolean(values.login || values.password || values.password_confirmation);
  return <Stack spacing={2}>
    <Typography color="text.secondary">Доступ ко входу — необязательно. Для выдачи доступа задайте логин и пароль. Письмо не требуется.</Typography>
    {(['login', 'password', 'password_confirmation'] as const).map((field) => {
      const Field = field === 'login' ? TextField : PasswordTextField;
      return <Field
        key={field} label={{ login: 'Логин для входа', password: 'Начальный пароль', password_confirmation: 'Повтор начального пароля' }[field]}
        autoComplete={field === 'login' ? 'username' : 'new-password'}
        value={values[field]} onChange={(e) => onChange(field, e.target.value)} disabled={disabled} required={required}
        inputProps={{ minLength: field === 'login' ? 3 : 12, maxLength: 128 }}
        helperText={field === 'password' ? 'От 12 до 128 символов' : undefined}
      />;
    })}
  </Stack>;
};
