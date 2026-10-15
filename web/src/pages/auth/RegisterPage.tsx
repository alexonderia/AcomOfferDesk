import { useEffect, useState } from 'react';
import { Button, CircularProgress, Stack, TextField } from '@mui/material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { inspectRegistrationInvitation, submitRegistration } from '@shared/api/auth/registration';
import { AuthPageShell } from '@shared/components/AuthPageShell';
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

  const canSubmit =
    login.trim().length >= 3 &&
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
    return (
      <AuthPageShell title="Регистрация по приглашению" maxWidth={560}>
        <Stack alignItems="center" sx={{ py: 2 }}>
          <CircularProgress size={28} />
        </Stack>
      </AuthPageShell>
    );
  }

  return (
    <AuthPageShell
      title="Регистрация по приглашению"
      subtitle="После подтверждения email вы зададите пароль на защищённой странице Acom."
      maxWidth={560}
    >
      <Stack spacing={2.5}>
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
    </AuthPageShell>
  );
};
