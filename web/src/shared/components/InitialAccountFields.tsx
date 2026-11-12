import { TextField } from '@mui/material';
import { AccountAccessSection } from './AccountAccessSection';
import { PasswordTextField } from './forms/PasswordTextField';
import { RequiredFieldLabel } from './forms/RequiredFieldLabel';

export type InitialAccountValues = { login: string; password: string; password_confirmation: string };

export const InitialAccountFields = ({ values, onChange, disabled = false }: {
  values: InitialAccountValues;
  onChange: (field: keyof InitialAccountValues, value: string) => void;
  disabled?: boolean;
}) => {
  const required = Boolean(values.login || values.password || values.password_confirmation);
  return <AccountAccessSection>
    {(['login', 'password', 'password_confirmation'] as const).map((field) => {
      const Field = field === 'login' ? TextField : PasswordTextField;
      const label = { login: 'Логин для входа', password: 'Начальный пароль', password_confirmation: 'Повтор начального пароля' }[field];
      const isPasswordValid = values.password.length >= 12 && values.password.length <= 128;
      const isValid = field === 'login'
        ? values.login.trim().length >= 3 && values.login.trim().length <= 128
        : isPasswordValid && (field === 'password' || values.password_confirmation === values.password);
      return <Field
        key={field} label={required ? <RequiredFieldLabel label={label} isValid={isValid} /> : label}
        InputLabelProps={{ required: false }}
        autoComplete={field === 'login' ? 'username' : 'new-password'}
        value={values[field]} onChange={(e) => onChange(field, e.target.value)} disabled={disabled} required={required}
        inputProps={{ minLength: field === 'login' ? 3 : 12, maxLength: 128 }}
        helperText={field === 'password' ? 'От 12 до 128 символов' : undefined}
      />;
    })}
  </AccountAccessSection>;
};
