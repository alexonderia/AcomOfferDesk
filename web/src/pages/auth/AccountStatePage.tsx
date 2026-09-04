import { Button, CircularProgress, Stack, TextField, Typography } from '@mui/material';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import {
  getRegistrationCurrentUserProfile,
  updateMyRegistrationCompanyContacts,
  updateMyRegistrationProfile,
} from '@shared/api/users/getCurrentUserProfile';
import { AuthPageShell } from '@shared/components/AuthPageShell';
import { RequiredFieldLabel } from '@shared/components/forms/RequiredFieldLabel';
import { ROLE } from '@shared/constants/roles';
import { textFieldAutocompleteProps } from '@shared/lib/forms';
import { formatRuPhone, isValidRuPhone } from '@shared/lib/phone';
import { resolveAuthenticatedPath } from '@shared/lib/routing/resolveAuthenticatedPath';
import { useSystemToasts, useToastMessageEffect } from '@shared/ui/toasts';
import { buildDraft, emptyDraft, type ProfileDraft } from './accountStateDraft';

type DraftErrors = Partial<Record<keyof ProfileDraft, string>>;

type StatusContent = {
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'error';
};

const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const innRegex = /^\d{10}$|^\d{12}$/;

const getStatusContent = (status: string, onboardingState: string | null): StatusContent => {
  if (onboardingState === 'first_login') {
    return {
      title: 'Заполните профиль',
      description: 'После сохранения данных откроется рабочий доступ.',
      severity: 'info'
    };
  }
  if (status === 'review') {
    return {
      title: 'Проверяем данные',
      description: '',
      severity: 'info'
    };
  }
  if (status === 'inactive') {
    return {
      title: 'Доступ к сайту закрыт',
      description: '',
      severity: 'warning'
    };
  }
  if (status === 'blacklist') {
    return {
      title: 'Доступ к сайту закрыт',
      description: '',
      severity: 'error'
    };
  }
  return {
    title: 'Ожидайте подтверждения',
    description: 'Мы уведомим вас, когда доступ будет открыт.',
    severity: 'info'
  };
};

const validateDraft = (draft: ProfileDraft, { requireCompany }: { requireCompany: boolean }): DraftErrors => {
  const errors: DraftErrors = {};
  const fullName = draft.fullName.trim();
  const phone = draft.phone.trim();
  const mail = draft.mail.trim();
  const companyName = draft.companyName.trim();
  const inn = draft.inn.trim();
  const companyPhone = draft.companyPhone.trim();
  const companyMail = draft.companyMail.trim();
  const address = draft.address.trim();
  const note = draft.note.trim();

  if (!fullName) {
    errors.fullName = 'Укажите ФИО';
  } else if (fullName.length > 256) {
    errors.fullName = 'Максимум 256 символов';
  }

  if (!phone) {
    errors.phone = 'Укажите телефон';
  } else if (!isValidRuPhone(phone)) {
    errors.phone = 'Некорректный формат телефона';
  }

  if (mail) {
    if (mail.length > 256) {
      errors.mail = 'Максимум 256 символов';
    } else if (!emailRegex.test(mail)) {
      errors.mail = 'Некорректный email';
    }
  }

  if (!requireCompany) {
    return errors;
  }

  if (!companyName) {
    errors.companyName = 'Укажите наименование компании';
  } else if (companyName.length > 256) {
    errors.companyName = 'Максимум 256 символов';
  }

  if (!inn) {
    errors.inn = 'Укажите ИНН';
  } else if (!innRegex.test(inn)) {
    errors.inn = 'ИНН должен содержать 10 или 12 цифр';
  }

  if (!companyPhone) {
    errors.companyPhone = 'Укажите телефон компании';
  } else if (!isValidRuPhone(companyPhone)) {
    errors.companyPhone = 'Некорректный формат телефона';
  }

  if (companyMail) {
    if (companyMail.length > 256) {
      errors.companyMail = 'Максимум 256 символов';
    } else if (!emailRegex.test(companyMail)) {
      errors.companyMail = 'Некорректный email';
    }
  }

  if (address.length > 256) {
    errors.address = 'Максимум 256 символов';
  }
  if (note.length > 1024) {
    errors.note = 'Максимум 1024 символа';
  }

  return errors;
};

export const AccountStatePage = () => {
  const navigate = useNavigate();
  const { session, logout, refresh } = useAuth();
  const { showErrorToast, showSuccessToast } = useSystemToasts();
  const [draft, setDraft] = useState<ProfileDraft>(emptyDraft);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showValidation, setShowValidation] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [touchedFields, setTouchedFields] = useState<Partial<Record<keyof ProfileDraft, boolean>>>({});
  const loadedUserIdRef = useRef<string | null>(null);

  const sessionUserId = session?.userId ?? null;
  const hasBusinessAccess = Boolean(session?.businessAccess);
  const isContractor = session?.roleId === ROLE.CONTRACTOR;
  const isFirstLogin = session?.onboardingState === 'first_login';
  const isReview = session?.status === 'review';
  const isBlocked = session?.status === 'inactive' || session?.status === 'blacklist';

  useToastMessageEffect({ message: !isBlocked ? errorMessage : null });

  useEffect(() => {
    if (!session) {
      navigate('/login', { replace: true });
      return;
    }
    if (hasBusinessAccess) {
      navigate(resolveAuthenticatedPath('/', session), { replace: true });
      return;
    }
  }, [hasBusinessAccess, navigate, session]);

  useEffect(() => {
    if (!session || hasBusinessAccess || !sessionUserId) {
      if (!session) {
        loadedUserIdRef.current = null;
      }
      return;
    }
    if (loadedUserIdRef.current === sessionUserId) {
      return;
    }

    loadedUserIdRef.current = sessionUserId;
    let cancelled = false;
    setIsLoading(true);
    setErrorMessage(null);
    void getRegistrationCurrentUserProfile()
      .then((data) => {
        if (cancelled) {
          return;
        }
        setDraft(buildDraft(data));
        setTouchedFields({});
        setShowValidation(false);
        setIsSubmitted(false);
      })
      .catch((error) => {
        if (!cancelled) {
          loadedUserIdRef.current = null;
          setErrorMessage(error instanceof Error ? error.message : 'Не удалось загрузить данные.');
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [hasBusinessAccess, session, sessionUserId]);

  const canEditCompany = useMemo(
    () => isContractor && (isReview || isFirstLogin),
    [isContractor, isFirstLogin, isReview],
  );
  const statusContent = useMemo(
    () => getStatusContent(session?.status ?? '', session?.onboardingState ?? null),
    [session?.onboardingState, session?.status],
  );
  const validationErrors = useMemo(
    () => validateDraft(draft, { requireCompany: canEditCompany }),
    [canEditCompany, draft]
  );
  const hasValue = (value: string) => Boolean(value.trim());
  const isFullNameFieldValid = hasValue(draft.fullName) && !validationErrors.fullName;
  const isPhoneFieldValid = hasValue(draft.phone) && !validationErrors.phone;
  const isCompanyNameFieldValid = hasValue(draft.companyName) && !validationErrors.companyName;
  const isInnFieldValid = hasValue(draft.inn) && !validationErrors.inn;
  const isCompanyPhoneFieldValid = hasValue(draft.companyPhone) && !validationErrors.companyPhone;

  const shouldShowFieldError = (field: keyof ProfileDraft) => {
    if (!validationErrors[field]) {
      return false;
    }
    return showValidation || Boolean(touchedFields[field]);
  };

  const getFieldHelperText = (field: keyof ProfileDraft) => {
    if (!shouldShowFieldError(field)) {
      return '';
    }
    return validationErrors[field] ?? '';
  };

  const markFieldTouched = (field: keyof ProfileDraft) => {
    setTouchedFields((prev) => ({ ...prev, [field]: true }));
  };

  const saveProfile = async () => {
    setErrorMessage(null);
    setShowValidation(true);
    if (Object.keys(validationErrors).length > 0) {
      setErrorMessage('Проверьте корректность заполнения полей.');
      return;
    }

    setIsSaving(true);
    try {
      const nextProfile = await updateMyRegistrationProfile({
        full_name: draft.fullName.trim(),
        phone: draft.phone.trim(),
        mail: draft.mail.trim() || undefined
      });
      if (canEditCompany) {
        const nextWithCompany = await updateMyRegistrationCompanyContacts({
          company_name: draft.companyName.trim(),
          inn: draft.inn.trim(),
          company_phone: draft.companyPhone.trim(),
          company_mail: draft.companyMail.trim() || undefined,
          address: draft.address.trim() || undefined,
          note: draft.note.trim() || undefined
        });
        setDraft(buildDraft(nextWithCompany));
      } else {
        setDraft(buildDraft(nextProfile));
      }
      setIsSubmitted(true);
      showSuccessToast(
        isFirstLogin
          ? 'Профиль сохранён. Рабочий доступ открыт.'
          : 'Данные переданы на проверку. Мы уведомим вас о выдаче доступа по электронной почте.',
      );
      if (isFirstLogin) {
        await refresh('bootstrap');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Не удалось сохранить данные';
      setErrorMessage(message);
      showErrorToast(message);
    } finally {
      setIsSaving(false);
    }
  };

  if (!session) {
    return null;
  }

  return (
    <AuthPageShell maxWidth={720}>
        {isLoading ? (
          <Stack alignItems="center" spacing={2}>
            <CircularProgress size={28} />
            <Typography variant="body2" color="text.secondary">
              {'Загружаем данные.'}
            </Typography>
          </Stack>
        ) : (
          <Stack spacing={2.5}>
            <Stack spacing={0.5}>
              <Typography variant="h5" fontWeight={700}>
                {statusContent.title}
              </Typography>
              {statusContent.description ? (
                <Typography variant="body2" color="text.secondary">
                  {statusContent.description}
                </Typography>
              ) : null}
            </Stack>
            {!isBlocked && !isSubmitted ? (
              <>
                <Stack spacing={1.5}>
                  <Typography variant="subtitle1" fontWeight={600}>{'Личные данные'}</Typography>
                  <TextField
                    label={<RequiredFieldLabel label="ФИО" isValid={isFullNameFieldValid} />}
                    value={draft.fullName}
                    {...textFieldAutocompleteProps('fullName')}
                    onBlur={() => markFieldTouched('fullName')}
                    onChange={(event) => {
                      setDraft((prev) => ({ ...prev, fullName: event.target.value }));
                      markFieldTouched('fullName');
                    }}
                    error={shouldShowFieldError('fullName')}
                    helperText={getFieldHelperText('fullName')}
                  />
                  <TextField
                    label={<RequiredFieldLabel label="Телефон" isValid={isPhoneFieldValid} />}
                    value={draft.phone}
                    {...textFieldAutocompleteProps('phone')}
                    onBlur={() => markFieldTouched('phone')}
                    onChange={(event) => {
                      setDraft((prev) => ({ ...prev, phone: formatRuPhone(event.target.value) }));
                      markFieldTouched('phone');
                    }}
                    error={shouldShowFieldError('phone')}
                    helperText={getFieldHelperText('phone')}
                  />
                  <TextField
                    label="E-mail"
                    value={draft.mail}
                    {...textFieldAutocompleteProps('mail')}
                    onBlur={() => markFieldTouched('mail')}
                    onChange={(event) => {
                      setDraft((prev) => ({ ...prev, mail: event.target.value }));
                      markFieldTouched('mail');
                    }}
                    error={shouldShowFieldError('mail')}
                    helperText={getFieldHelperText('mail')}
                  />
                </Stack>

                {canEditCompany ? (
                  <Stack spacing={1.5}>
                    <Typography variant="subtitle1" fontWeight={600}>{'Данные компании'}</Typography>
                    <TextField
                      label={<RequiredFieldLabel label="Компания" isValid={isCompanyNameFieldValid} />}
                      value={draft.companyName}
                      {...textFieldAutocompleteProps('companyName')}
                      onBlur={() => markFieldTouched('companyName')}
                      onChange={(event) => {
                        setDraft((prev) => ({ ...prev, companyName: event.target.value }));
                        markFieldTouched('companyName');
                      }}
                      error={shouldShowFieldError('companyName')}
                      helperText={getFieldHelperText('companyName')}
                    />
                    <TextField
                      label={<RequiredFieldLabel label="ИНН" isValid={isInnFieldValid} />}
                      value={draft.inn}
                      {...textFieldAutocompleteProps('inn')}
                      onBlur={() => markFieldTouched('inn')}
                      onChange={(event) => {
                        setDraft((prev) => ({ ...prev, inn: event.target.value.replace(/\D/g, '') }));
                        markFieldTouched('inn');
                      }}
                      error={shouldShowFieldError('inn')}
                      helperText={getFieldHelperText('inn')}
                    />
                    <TextField
                      label={<RequiredFieldLabel label="Телефон компании" isValid={isCompanyPhoneFieldValid} />}
                      value={draft.companyPhone}
                      {...textFieldAutocompleteProps('companyPhone')}
                      onBlur={() => markFieldTouched('companyPhone')}
                      onChange={(event) => {
                        setDraft((prev) => ({ ...prev, companyPhone: formatRuPhone(event.target.value) }));
                        markFieldTouched('companyPhone');
                      }}
                      error={shouldShowFieldError('companyPhone')}
                      helperText={getFieldHelperText('companyPhone')}
                    />
                    <TextField
                      label="E-mail компании"
                      value={draft.companyMail}
                      {...textFieldAutocompleteProps('companyMail')}
                      onBlur={() => markFieldTouched('companyMail')}
                      onChange={(event) => {
                        setDraft((prev) => ({ ...prev, companyMail: event.target.value }));
                        markFieldTouched('companyMail');
                      }}
                      error={shouldShowFieldError('companyMail')}
                      helperText={getFieldHelperText('companyMail')}
                    />
                    <TextField
                      label="Адрес"
                      value={draft.address}
                      {...textFieldAutocompleteProps('address')}
                      onBlur={() => markFieldTouched('address')}
                      onChange={(event) => {
                        setDraft((prev) => ({ ...prev, address: event.target.value }));
                        markFieldTouched('address');
                      }}
                      error={shouldShowFieldError('address')}
                      helperText={getFieldHelperText('address')}
                    />
                    <TextField
                      label="Примечание"
                      value={draft.note}
                      multiline
                      minRows={3}
                      {...textFieldAutocompleteProps('note')}
                      onBlur={() => markFieldTouched('note')}
                      onChange={(event) => {
                        setDraft((prev) => ({ ...prev, note: event.target.value }));
                        markFieldTouched('note');
                      }}
                      error={shouldShowFieldError('note')}
                      helperText={getFieldHelperText('note')}
                    />
                  </Stack>
                ) : null}

                <Button
                  variant="contained"
                  onClick={() => void saveProfile()}
                  disabled={isSaving}
                  sx={{ alignSelf: 'flex-start', textTransform: 'none', boxShadow: 'none' }}
                >
                  {isSaving ? 'Сохраняем...' : 'Отправить данные'}
                </Button>
              </>
            ) : null}

            <Stack direction="row" spacing={1.5}>
              <Button variant="outlined" onClick={logout} sx={{ textTransform: 'none' }}>
                {'Выйти'}
              </Button>
            </Stack>
          </Stack>
        )}
    </AuthPageShell>
  );
};
