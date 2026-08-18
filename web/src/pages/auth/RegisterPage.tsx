import { useEffect, useState } from 'react';
import { Box, Button, Paper, Stack, TextField, Typography } from '@mui/material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { inspectRegistrationInvitation, submitRegistration } from '@shared/api/auth/registration';
import { RequiredFieldLabel } from '@shared/components/forms/RequiredFieldLabel';
import { formatRuPhone, isValidRuPhone } from '@shared/lib/phone';
import { useSystemToasts } from '@shared/ui/toasts';

const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const innRegex = /^\d{10}$|^\d{12}$/;

export const RegisterPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { showErrorToast, showSuccessToast } = useSystemToasts();
  const token = searchParams.get('token')?.trim() ?? '';
  const [email, setEmail] = useState('');
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [inn, setInn] = useState('');
  const [companyPhone, setCompanyPhone] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [loginLocked, setLoginLocked] = useState(false);

  useEffect(() => {
    if (!token) {
      navigate('/auth/registration-link-status?reason=invalid', { replace: true });
      return;
    }
    let cancelled = false;
    void inspectRegistrationInvitation(token)
      .then((response) => {
        if (cancelled) {
          return;
        }
        const status = response.data.status;
        if (status === 'expired') {
          navigate('/auth/registration-link-status?reason=expired', { replace: true });
          return;
        }
        if (status === 'consumed' || status === 'already_registered') {
          navigate('/auth/registration-link-status?reason=already_registered', { replace: true });
          return;
        }
        if ((status === 'ok' || status === 'in_progress') && response.data.email) {
          setEmail(response.data.email);
          if (status === 'in_progress') {
            setLogin(response.data.login ?? '');
            setLoginLocked(Boolean(response.data.login));
            setFullName(response.data.full_name ?? '');
            setPhone(formatRuPhone(response.data.phone ?? ''));
            setCompanyName(response.data.company_name ?? '');
            setInn(response.data.inn ?? '');
            setCompanyPhone(formatRuPhone(response.data.company_phone ?? ''));
          }
          setIsLoading(false);
          return;
        }
        navigate('/auth/registration-link-status?reason=invalid', { replace: true });
      })
      .catch(() => {
        if (!cancelled) {
          navigate('/auth/registration-link-status?reason=invalid', { replace: true });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [navigate, token]);

  const passwordValid = password.length >= 12 && password.length <= 128;
  const passwordsMatch = password === passwordConfirmation && passwordValid;
  const canSubmit =
    login.trim().length >= 3 &&
    passwordsMatch &&
    Boolean(fullName.trim()) &&
    isValidRuPhone(phone) &&
    Boolean(companyName.trim()) &&
    innRegex.test(inn.trim()) &&
    isValidRuPhone(companyPhone) &&
    emailRegex.test(email);

  const submit = async () => {
    if (!canSubmit) {
      showErrorToast('Заполните обязательные поля');
      return;
    }
    setIsSaving(true);
    try {
      const result = await submitRegistration({
        token,
        login: login.trim(),
        password,
        password_confirmation: passwordConfirmation,
        email,
        full_name: fullName.trim(),
        phone: phone.trim(),
        company_name: companyName.trim(),
        inn: inn.trim(),
        company_phone: companyPhone.trim(),
      });
      showSuccessToast(result.detail);
      navigate(`/verify-email?next=check_email&invite=${encodeURIComponent(token)}`, { replace: true });
    } catch (error) {
      showErrorToast(error instanceof Error ? error.message : 'Не удалось завершить регистрацию');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return null;
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 3 }}>
      <Paper
        elevation={0}
        sx={(theme) => ({
          width: { xs: '94%', sm: 560 },
          borderRadius: 3,
          border: `1px solid ${theme.palette.divider}`,
          backgroundColor: theme.palette.background.paper,
          padding: { xs: 4, sm: 5 },
        })}
      >
        <Stack spacing={2.5}>
          <Typography variant="h5" fontWeight={700} textAlign="center">
            Регистрация по приглашению
          </Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Если email указан неверно, измените его до подтверждения. Пароль — от 12 до 128 символов.
          </Typography>
          <TextField
            label="Email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            fullWidth
          />
          <TextField
            label={<RequiredFieldLabel isValid={login.trim().length >= 3} label="Логин" />}
            value={login}
            onChange={(event) => setLogin(event.target.value)}
            autoComplete="username"
            InputProps={{ readOnly: loginLocked }}
            fullWidth
          />
          <TextField
            label={<RequiredFieldLabel isValid={passwordValid} label="Пароль" />}
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="new-password"
            fullWidth
          />
          <TextField
            label={<RequiredFieldLabel isValid={passwordsMatch} label="Повторите пароль" />}
            type="password"
            value={passwordConfirmation}
            onChange={(event) => setPasswordConfirmation(event.target.value)}
            autoComplete="new-password"
            fullWidth
          />
          <TextField
            label={<RequiredFieldLabel isValid={Boolean(fullName.trim())} label="ФИО" />}
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            fullWidth
          />
          <TextField
            label={<RequiredFieldLabel isValid={isValidRuPhone(phone)} label="Телефон" />}
            value={phone}
            onChange={(event) => setPhone(formatRuPhone(event.target.value))}
            fullWidth
          />
          <TextField
            label={<RequiredFieldLabel isValid={Boolean(companyName.trim())} label="Компания" />}
            value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
            fullWidth
          />
          <TextField
            label={<RequiredFieldLabel isValid={innRegex.test(inn.trim())} label="ИНН" />}
            value={inn}
            onChange={(event) => setInn(event.target.value)}
            fullWidth
          />
          <TextField
            label={<RequiredFieldLabel isValid={isValidRuPhone(companyPhone)} label="Телефон компании" />}
            value={companyPhone}
            onChange={(event) => setCompanyPhone(formatRuPhone(event.target.value))}
            fullWidth
          />
          <Button variant="contained" disabled={isSaving || !canSubmit} onClick={() => void submit()}>
            Отправить заявку
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
};
