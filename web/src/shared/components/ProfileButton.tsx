import EditOutlined from '@mui/icons-material/EditOutlined';
import PersonOutlineRounded from '@mui/icons-material/PersonOutlineRounded';
import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogContent,
  Divider,
  FormControlLabel,
  Stack,
  Switch,
  Tooltip,
  Typography
} from '@mui/material';
import { type Theme, useTheme } from '@mui/material/styles';
import { useAuth } from '@app/providers/AuthProvider';
import { UnavailabilityManagementSection, UnavailabilityPeriodEditor } from '@entities/unavailability';
import { ActionButton } from '@shared/components/ActionButton';
import { ValidatedTextField } from '@shared/components/forms/ValidatedTextField';
import { requestEmailVerification } from '@shared/api/auth/emailVerification';
import {
  getCurrentUserProfile,
  getMyNotificationPreferences,
  linkMyMaxAccount,
  setMyUnavailabilityPeriod,
  type CurrentUserProfile,
  type NotificationPreferences,
  type NotificationPreferencesMode,
  updateMyCompanyContacts,
  updateMyCredentials,
  updateMyNotificationPreferences,
  updateMyProfile
} from '@shared/api/users/getCurrentUserProfile';
import { ROLE } from '@shared/constants/roles';
import { useLiveValidatedForm } from '@shared/lib/forms';
import { useSystemToasts } from '@shared/ui/toasts';
import { z } from 'zod';

const fallbackText = 'Не указано';
const defaultDbPlaceholder = 'не указано';

const dialogPaperSx = (theme: Theme) => ({
  borderRadius: 2,
  px: { xs: 2.5, sm: 3.5 },
  py: { xs: 3, sm: 3.5 },
  backgroundColor: theme.palette.background.default,
  maxHeight: 'min(760px, calc(100vh - 32px))',
  overflow: 'hidden',
  boxShadow:
    theme.palette.mode === 'light'
      ? '0 24px 80px rgba(15, 23, 42, 0.18)'
      : '0 24px 80px rgba(0, 0, 0, 0.5)'
});

const dialogContentSx = {
  p: 0,
  overflowX: 'hidden',
  overflowY: 'auto',
  scrollbarWidth: 'none',
  '&::-webkit-scrollbar': {
    display: 'none'
  }
};

const inputFieldSx = {
  '& .MuiOutlinedInput-root': {
    borderRadius: 1,
    backgroundColor: 'background.paper'
  }
};

const smallEditButtonSx = {
  borderRadius: 1,
  textTransform: 'none',
  minWidth: 0,
  px: 1.25
};

const primaryButtonSx = {
  borderRadius: 1,
  textTransform: 'none',
  py: 1.1,
  boxShadow: 'none'
};

const submitButtonSx = {
  borderRadius: 1,
  textTransform: 'none',
  py: 1.25,
  fontSize: 16,
  fontWeight: 700,
  boxShadow: 'none'
};

const notificationSwitchSx = {
  m: 0,
  justifyContent: 'space-between',
  width: '100%',
  '& .MuiFormControlLabel-label': {
    fontSize: 15
  },
  '& .MuiSwitch-root': {
    width: 46,
    height: 28,
    p: 0
  },
  '& .MuiSwitch-switchBase': {
    p: '4px',
    '&.Mui-checked': {
      transform: 'translateX(18px)',
      color: '#fff',
      '& + .MuiSwitch-track': {
        opacity: 1,
        backgroundColor: 'primary.main',
        borderColor: 'primary.main'
      }
    }
  },
  '& .MuiSwitch-thumb': {
    width: 20,
    height: 20,
    boxShadow: 'none'
  },
  '& .MuiSwitch-track': {
    borderRadius: '999px',
    opacity: 1,
    backgroundColor: 'action.selected',
    border: '1px solid',
    borderColor: 'divider'
  }
};

const isPlaceholderValue = (value: string) => value.trim().toLowerCase() === defaultDbPlaceholder;

const optionalEmail = z
  .string()
  .trim()
  .refine(
    (value) => value.length === 0 || isPlaceholderValue(value) || z.string().email().safeParse(value).success,
    'Введите корректный email'
  );

const passwordSchema = z
  .object({
    oldPassword: z.string().min(1, 'Введите текущий пароль'),
    password: z.string().min(8, 'Минимум 8 символов'),
    confirmPassword: z.string().min(1, 'Повторите пароль')
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: 'Пароли не совпадают',
    path: ['confirmPassword']
  });

const profileSchema = z.object({
  full_name: z.string().trim().min(1, 'Введите ФИО'),
  phone: z.string().trim().min(1, 'Введите телефон'),
  mail: optionalEmail
});

const maxLinkSchema = z.object({
  code: z.string().trim().min(1, 'Введите MAX ID')
});

const companySchema = z.object({
  inn: z.string().trim().min(1, 'Введите ИНН'),
  company_name: z.string().trim().min(1, 'Введите наименование'),
  company_phone: z.string().trim().min(1, 'Введите телефон'),
  company_mail: optionalEmail,
  address: z.string().trim(),
  note: z.string().trim()
});

const unavailabilitySchema = z
  .object({
    status: z.enum(['sick', 'vacation', 'fired', 'maternity', 'business_trip', 'unavailable']),
    started_at: z.string().min(1, 'Выберите дату начала'),
    ended_at: z.string().min(1, 'Выберите дату окончания')
  })
  .refine((values) => new Date(values.ended_at).getTime() >= new Date(values.started_at).getTime(), {
    message: 'Дата окончания должна быть не раньше даты начала',
    path: ['ended_at']
  });

type PasswordFormValues = z.infer<typeof passwordSchema>;
type ProfileFormValues = z.infer<typeof profileSchema>;
type MaxLinkFormValues = z.infer<typeof maxLinkSchema>;
type CompanyFormValues = z.infer<typeof companySchema>;
type UnavailabilityFormValues = z.infer<typeof unavailabilitySchema>;

type ProfileButtonProps = {
  iconOnly?: boolean;
  sidebar?: boolean;
};

const DataRow = ({ label, value }: { label: string; value: string | null }) => (
  <Stack
    direction={{ xs: 'column', sm: 'row' }}
    spacing={{ xs: 0.5, sm: 2 }}
    alignItems={{ xs: 'flex-start', sm: 'center' }}
  >
    <Typography sx={{ width: { sm: 170 }, color: 'text.primary' }}>{label}</Typography>
    <Typography color={value ? 'text.primary' : 'text.secondary'}>{value ?? fallbackText}</Typography>
  </Stack>
);

const normalizeOptional = (value: string) => {
  const trimmed = value.trim();
  if (trimmed.length === 0 || isPlaceholderValue(trimmed)) {
    return undefined;
  }
  return trimmed;
};

const sanitizeDefaultValue = (value: string | null) => (value && isPlaceholderValue(value) ? '' : value ?? '');

export const ProfileButton = ({ iconOnly = false, sidebar = false }: ProfileButtonProps) => {
  const theme = useTheme();
  const { session } = useAuth();
  const { showSuccessToast, showSystemToast } = useSystemToasts();
  const [open, setOpen] = useState(false);
  const [openPassword, setOpenPassword] = useState(false);
  const [openProfile, setOpenProfile] = useState(false);
  const [openCompany, setOpenCompany] = useState(false);
  const [openUnavailability, setOpenUnavailability] = useState(false);
  const [profile, setProfile] = useState<CurrentUserProfile | null>(null);
  const [notificationPreferences, setNotificationPreferences] = useState<NotificationPreferences | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSavingNotificationPreferences, setIsSavingNotificationPreferences] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register: registerPassword,
    handleSubmit: handlePasswordSubmit,
    formState: { errors: passwordErrors, isSubmitting: isSubmittingPassword },
    reset: resetPassword
  } = useLiveValidatedForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { oldPassword: '', password: '', confirmPassword: '' }
  });

  const {
    register: registerProfile,
    handleSubmit: handleProfileSubmit,
    formState: { errors: profileErrors, isSubmitting: isSubmittingProfile },
    reset: resetProfile
  } = useLiveValidatedForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { full_name: '', phone: '', mail: '' }
  });

  const {
    register: registerCompany,
    handleSubmit: handleCompanySubmit,
    formState: { errors: companyErrors, isSubmitting: isSubmittingCompany },
    reset: resetCompany
  } = useLiveValidatedForm<CompanyFormValues>({
    resolver: zodResolver(companySchema),
    defaultValues: { inn: '', company_name: '', company_phone: '', company_mail: '', address: '', note: '' }
  });

  const {
    register: registerMaxLink,
    handleSubmit: handleMaxLinkSubmit,
    formState: { errors: maxLinkErrors, isSubmitting: isSubmittingMaxLink },
    reset: resetMaxLink
  } = useLiveValidatedForm<MaxLinkFormValues>({
    resolver: zodResolver(maxLinkSchema),
    defaultValues: { code: '' }
  });

  const {
    register: registerUnavailability,
    handleSubmit: handleUnavailabilitySubmit,
    watch: watchUnavailability,
    setValue: setUnavailabilityValue,
    formState: { errors: unavailabilityErrors, isSubmitting: isSubmittingUnavailability },
    reset: resetUnavailability
  } = useLiveValidatedForm<UnavailabilityFormValues>({
    resolver: zodResolver(unavailabilitySchema),
    defaultValues: { status: 'unavailable', started_at: '', ended_at: '' }
  });

  useEffect(() => {
    if (!profile) {
      return;
    }

    resetProfile({
      full_name: profile.fullName ?? '',
      phone: profile.phone ?? '',
      mail: sanitizeDefaultValue(profile.mail)
    });

    resetCompany({
      inn: profile.company.inn ?? '',
      company_name: profile.company.companyName ?? '',
      company_phone: profile.company.phone ?? '',
      company_mail: sanitizeDefaultValue(profile.company.mail),
      address: sanitizeDefaultValue(profile.company.address),
      note: sanitizeDefaultValue(profile.company.note)
    });

    resetUnavailability({
      status: 'unavailable',
      started_at: '',
      ended_at: ''
    });
    resetMaxLink({ code: '' });
  }, [profile, resetCompany, resetMaxLink, resetProfile, resetUnavailability]);

  const loadProfile = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getCurrentUserProfile();
      const preferences = await getMyNotificationPreferences();
      setProfile(data);
      setNotificationPreferences(preferences);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Не удалось загрузить профиль');
    } finally {
      setIsLoading(false);
    }
  };

  const openDialog = async () => {
    setOpen(true);
    if (isLoading || profile) {
      return;
    }
    await loadProfile();
  };

  const showCompanyInfo = (profile?.roleId ?? session?.roleId) === ROLE.CONTRACTOR;
  const showContractorNotificationSettings = (profile?.roleId ?? session?.roleId) === ROLE.CONTRACTOR;
  const canEditCredentials = Boolean(profile?.actions.manage_credentials) && session?.authProvider === 'legacy';
  const canEditProfile = Boolean(profile?.actions.manage_own_profile);
  const canEditCompany = Boolean(profile?.actions.manage_company_contacts);
  const canSetUnavailability = Boolean(profile?.actions.manage_own_unavailability);

  const onSubmitPassword = async (values: PasswordFormValues) => {
    setError(null);
    try {
      const nextProfile = await updateMyCredentials({
        current_password: values.oldPassword.trim(),
        new_password: values.password.trim()
      });
      setProfile(nextProfile);
      resetPassword({ oldPassword: '', password: '', confirmPassword: '' });
      setOpenPassword(false);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Не удалось обновить пароль');
    }
  };

  const onSubmitProfile = async (values: ProfileFormValues) => {
    setError(null);
    try {
      const normalizedMail = normalizeOptional(values.mail);
      const currentMail = normalizeOptional(profile?.mail ?? '');
      const normalizedMailLower = normalizedMail?.toLowerCase();
      const currentMailLower = currentMail?.toLowerCase() ?? '';
      const shouldRequestVerification = Boolean(normalizedMailLower) && normalizedMailLower !== currentMailLower;
      const nextProfile = await updateMyProfile({
        full_name: values.full_name.trim(),
        phone: values.phone.trim()
      });
      let verificationDetail: string | null = null;
      if (shouldRequestVerification && normalizedMail) {
        const verificationResult = await requestEmailVerification(normalizedMail);
        verificationDetail = verificationResult.detail;
      }
      setProfile(nextProfile);
      setOpenProfile(false);
      if (verificationDetail) {
        showSystemToast({ severity: 'info', message: verificationDetail });
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Не удалось обновить личные данные');
    }
  };

  const onSubmitCompany = async (values: CompanyFormValues) => {
    setError(null);
    try {
      const nextProfile = await updateMyCompanyContacts({
        inn: values.inn.trim(),
        company_name: values.company_name.trim(),
        company_phone: values.company_phone.trim(),
        company_mail: normalizeOptional(values.company_mail),
        address: normalizeOptional(values.address),
        note: normalizeOptional(values.note)
      });
      setProfile(nextProfile);
      setOpenCompany(false);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Не удалось обновить данные компании');
    }
  };

  const onSubmitMaxLink = async (values: MaxLinkFormValues) => {
    setError(null);
    try {
      const nextProfile = await linkMyMaxAccount({
        code: values.code.trim()
      });
      const nextPreferences = await getMyNotificationPreferences();
      setProfile(nextProfile);
      setNotificationPreferences(nextPreferences);
      resetMaxLink({ code: '' });
      showSuccessToast('MAX привязан к вашему аккаунту.');
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Не удалось привязать MAX');
    }
  };

  const saveNotificationMode = async (mode: NotificationPreferencesMode) => {
    setError(null);
    setIsSavingNotificationPreferences(true);
    try {
      const nextPreferences = await updateMyNotificationPreferences({ mode });
      setNotificationPreferences(nextPreferences);
      showSuccessToast('Настройки уведомлений сохранены.');
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Не удалось сохранить настройки уведомлений');
    } finally {
      setIsSavingNotificationPreferences(false);
    }
  };

  const handleNotificationChannelsChange = (channel: 'email' | 'max', checked: boolean) => {
    if (!notificationPreferences) {
      return;
    }

    const currentEmailEnabled =
      notificationPreferences.mode === 'all' || notificationPreferences.mode === 'email_only';
    const currentMaxEnabled =
      notificationPreferences.mode === 'all' || notificationPreferences.mode === 'max_only';

    const nextEmailEnabled = channel === 'email' ? checked : currentEmailEnabled;
    const nextMaxEnabled = channel === 'max' ? checked : currentMaxEnabled;

    let nextMode: NotificationPreferencesMode = 'none';
    if (nextEmailEnabled && nextMaxEnabled) {
      nextMode = 'all';
    } else if (nextEmailEnabled) {
      nextMode = 'email_only';
    } else if (nextMaxEnabled) {
      nextMode = 'max_only';
    }

    void saveNotificationMode(nextMode);
  };

  const onSubmitUnavailability = async (values: UnavailabilityFormValues) => {
    setError(null);
    try {
      const nextProfile = await setMyUnavailabilityPeriod({
        status: values.status,
        started_at: new Date(values.started_at).toISOString(),
        ended_at: new Date(values.ended_at).toISOString()
      });
      setProfile(nextProfile);
      setOpenUnavailability(false);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Не удалось обновить нерабочий период');
    }
  };

  const isEmailNotificationsEnabled =
    notificationPreferences?.mode === 'all' || notificationPreferences?.mode === 'email_only';
  const isMaxNotificationsEnabled =
    notificationPreferences?.mode === 'all' || notificationPreferences?.mode === 'max_only';

  return (
    <>
      {sidebar ? (
        <Tooltip title="Профиль" placement="right" enterDelay={150} disableHoverListener={!iconOnly}>
          <Box component="span" sx={{ display: 'block', width: '100%' }}>
            <ActionButton
              kind="custom"
              showNavigationIcons={false}
              onClick={() => void openDialog()}
              aria-label="Открыть профиль"
              sx={{
                width: '100%',
                minHeight: 42,
                minWidth: 0,
                borderRadius: `${theme.acomShape.buttonRadius}px !important`,
                justifyContent: iconOnly ? 'center' : 'flex-start',
                px: iconOnly ? 0 : 1.75,
                gap: iconOnly ? 0 : 1.25,
                transition: 'padding 0.32s ease, gap 0.32s ease'
              }}
            >
              <Box component="span" sx={{ display: 'inline-flex', lineHeight: 1 }}>
                <PersonOutlineRounded fontSize="small" />
              </Box>
              <Typography
                sx={{
                  maxWidth: iconOnly ? 0 : 160,
                  opacity: iconOnly ? 0 : 1,
                  transform: iconOnly ? 'translateX(-4px)' : 'translateX(0)',
                  overflow: 'hidden',
                  textOverflow: 'clip',
                  whiteSpace: 'nowrap',
                  fontSize: 14,
                  fontWeight: 500,
                  lineHeight: 1.2,
                  transition: 'max-width 0.34s ease, opacity 0.24s ease, transform 0.34s ease'
                }}
              >
                Профиль
              </Typography>
            </ActionButton>
          </Box>
        </Tooltip>
      ) : iconOnly ? (
        <Tooltip title="Профиль" placement="right" enterDelay={150}>
          <Box component="span" sx={{ display: 'block', width: '100%' }}>
            <ActionButton
              kind="custom"
              showNavigationIcons={false}
              onClick={() => void openDialog()}
              aria-label="Открыть профиль"
              sx={{
                width: '100%',
                minHeight: 42,
                minWidth: 0,
                borderRadius: `${theme.acomShape.buttonRadius}px !important`,
                justifyContent: 'center',
                px: 0,
                gap: 0
              }}
            >
              <Box component="span" sx={{ display: 'inline-flex', lineHeight: 1 }}>
                <PersonOutlineRounded fontSize="small" />
              </Box>
            </ActionButton>
          </Box>
        </Tooltip>
      ) : (
        <Button variant="outlined" onClick={() => void openDialog()} startIcon={<PersonOutlineRounded fontSize="small" />} sx={{ minWidth: 124 }}>
          Профиль
        </Button>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth PaperProps={{ sx: dialogPaperSx }}>
        <DialogContent sx={dialogContentSx}>
          {isLoading ? (
            <Stack alignItems="center" justifyContent="center" sx={{ minHeight: 240 }}>
              <CircularProgress size={28} />
            </Stack>
          ) : (
            <Stack spacing={2}>
              {error ? <Alert severity="error">{error}</Alert> : null}

              <Stack spacing={1.5}>
                <Stack
                  direction={{ xs: 'column', sm: 'row' }}
                  spacing={1}
                  alignItems={{ xs: 'flex-start', sm: 'center' }}
                  justifyContent="space-between"
                >
                  <Typography variant="h5" fontWeight={600} lineHeight={1}>
                    Личные данные
                  </Typography>
                  <Stack direction="row" spacing={1}>
                    {canEditCredentials ? (
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<EditOutlined fontSize="small" />}
                        sx={smallEditButtonSx}
                        onClick={() => setOpenPassword(true)}
                      />
                    ) : null}
                    {canEditProfile ? (
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<EditOutlined fontSize="small" />}
                        sx={smallEditButtonSx}
                        onClick={() => setOpenProfile(true)}
                      />
                    ) : null}
                  </Stack>
                </Stack>
                <DataRow label="Логин" value={session?.login ?? profile?.userId ?? null} />
                <DataRow label="ФИО" value={profile?.fullName ?? null} />
                <DataRow label="Телефон" value={profile?.phone ?? null} />
                <DataRow label="E-mail" value={profile?.mail ?? null} />
              </Stack>

              {showCompanyInfo ? <Divider /> : null}

              {canSetUnavailability ? (
                <Stack spacing={1.5}>
                  <UnavailabilityManagementSection
                    currentPeriod={profile?.unavailablePeriod ?? null}
                    periods={profile?.unavailablePeriods ?? []}
                    canEdit
                    isDialogOpen={openUnavailability}
                    onOpenDialog={() => setOpenUnavailability(true)}
                    onCloseDialog={() => setOpenUnavailability(false)}
                    onSubmit={handleUnavailabilitySubmit((values) => void onSubmitUnavailability(values))}
                    isSubmitting={isSubmittingUnavailability}
                    dialogTitle="Установить нерабочий период"
                    triggerLabel="Установить нерабочий период"
                    submitLabel="Сохранить период"
                    editor={
                      <UnavailabilityPeriodEditor
                        statusField={registerUnavailability('status')}
                        startedAtField={registerUnavailability('started_at')}
                        endedAtField={registerUnavailability('ended_at')}
                        startedAtValue={watchUnavailability('started_at') ?? ''}
                        endedAtValue={watchUnavailability('ended_at') ?? ''}
                        onStartedAtChange={(value: string) =>
                          setUnavailabilityValue('started_at', value, { shouldValidate: true, shouldDirty: true })
                        }
                        onEndedAtChange={(value: string) =>
                          setUnavailabilityValue('ended_at', value, { shouldValidate: true, shouldDirty: true })
                        }
                        statusError={unavailabilityErrors.status?.message}
                        startedAtError={unavailabilityErrors.started_at?.message}
                        endedAtError={unavailabilityErrors.ended_at?.message}
                      />
                    }
                  />
                </Stack>
              ) : null}

              {showCompanyInfo ? (
                <Stack spacing={1.5}>
                  <Stack
                    direction={{ xs: 'column', sm: 'row' }}
                    spacing={1}
                    alignItems={{ xs: 'flex-start', sm: 'center' }}
                    justifyContent="space-between"
                  >
                    <Typography variant="h5" fontWeight={600} lineHeight={1}>
                      Данные компании
                    </Typography>
                    {canEditCompany ? (
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<EditOutlined fontSize="small" />}
                        sx={smallEditButtonSx}
                        onClick={() => setOpenCompany(true)}
                      />
                    ) : null}
                  </Stack>
                  <DataRow label="ИНН" value={profile?.company.inn ?? null} />
                  <DataRow label="Наименование" value={profile?.company.companyName ?? null} />
                  <DataRow label="Телефон" value={profile?.company.phone ?? null} />
                  <DataRow label="E-mail" value={profile?.company.mail ?? null} />
                  <DataRow label="Адрес" value={profile?.company.address ?? null} />
                  <DataRow label="Доп. информация" value={profile?.company.note ?? null} />
                </Stack>
              ) : null}

              {canEditProfile && showContractorNotificationSettings ? <Divider /> : null}

              {canEditProfile && showContractorNotificationSettings ? (
                <Stack spacing={1.5} component="form" onSubmit={handleMaxLinkSubmit((values) => void onSubmitMaxLink(values))}>
                  <Typography variant="h5" fontWeight={600} lineHeight={1}>
                    Привязка MAX
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    По команде `/start` в MAX-боте можно узнать свой MAX ID и по нему привязать аккаунт для уведомлений.
                  </Typography>
                  <ValidatedTextField
                    label="MAX ID"
                    fieldName="code"
                    registration={registerMaxLink('code')}
                    error={Boolean(maxLinkErrors.code)}
                    helperText={maxLinkErrors.code?.message}
                    sx={inputFieldSx}
                  />
                  <Button type="submit" variant="contained" sx={primaryButtonSx} disabled={isSubmittingMaxLink}>
                    Привязать MAX
                  </Button>
                </Stack>
              ) : null}

              {canEditProfile && showContractorNotificationSettings && notificationPreferences ? <Divider /> : null}

              {canEditProfile && showContractorNotificationSettings && notificationPreferences ? (
                <Stack spacing={1.5}>
                  <Typography variant="h5" fontWeight={600} lineHeight={1}>
                    Уведомления
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Выберите, как получать уведомления.
                  </Typography>
                  <Stack spacing={0.5}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={Boolean(isEmailNotificationsEnabled)}
                          onChange={(_, checked) => handleNotificationChannelsChange('email', checked)}
                          disabled={!notificationPreferences.emailAvailable || isSavingNotificationPreferences}
                        />
                      }
                      label={`Email${notificationPreferences?.email ? `: ${notificationPreferences.email}` : ''}`}
                      labelPlacement="start"
                      sx={notificationSwitchSx}
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={Boolean(isMaxNotificationsEnabled)}
                          onChange={(_, checked) => handleNotificationChannelsChange('max', checked)}
                          disabled={!notificationPreferences.maxAvailable || isSavingNotificationPreferences}
                        />
                      }
                      label={`MAX${notificationPreferences?.maxUserId ? `: ${notificationPreferences.maxUserId}` : ''}`}
                      labelPlacement="start"
                      sx={notificationSwitchSx}
                    />
                  </Stack>
                </Stack>
              ) : null}
            </Stack>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={openPassword} onClose={() => setOpenPassword(false)} fullWidth maxWidth="sm" PaperProps={{ sx: dialogPaperSx }}>
        <DialogContent sx={dialogContentSx}>
          <Stack spacing={2} component="form" onSubmit={handlePasswordSubmit((values) => void onSubmitPassword(values))}>
            <Typography variant="h5" fontWeight={600} lineHeight={1}>
              Изменение пароля
            </Typography>
            <ValidatedTextField
              label="Старый пароль"
              type="password"
              fieldName="oldPassword"
              registration={registerPassword('oldPassword')}
              error={Boolean(passwordErrors.oldPassword)}
              helperText={passwordErrors.oldPassword?.message}
              sx={inputFieldSx}
            />
            <ValidatedTextField
              label="Новый пароль"
              type="password"
              fieldName="password"
              registration={registerPassword('password')}
              error={Boolean(passwordErrors.password)}
              helperText={passwordErrors.password?.message}
              sx={inputFieldSx}
            />
            <ValidatedTextField
              label="Повторите новый пароль"
              type="password"
              fieldName="confirmPassword"
              registration={registerPassword('confirmPassword')}
              error={Boolean(passwordErrors.confirmPassword)}
              helperText={passwordErrors.confirmPassword?.message}
              sx={inputFieldSx}
            />
            <Button type="submit" variant="contained" fullWidth sx={submitButtonSx} disabled={isSubmittingPassword}>
              Сохранить новый пароль
            </Button>
          </Stack>
        </DialogContent>
      </Dialog>

      <Dialog open={openProfile} onClose={() => setOpenProfile(false)} fullWidth maxWidth="sm" PaperProps={{ sx: dialogPaperSx }}>
        <DialogContent sx={dialogContentSx}>
          <Stack spacing={2} component="form" onSubmit={handleProfileSubmit((values) => void onSubmitProfile(values))}>
            <Typography variant="h5" fontWeight={600} lineHeight={1}>
              Личные данные
            </Typography>
            <ValidatedTextField
              label="ФИО"
              fieldName="full_name"
              registration={registerProfile('full_name')}
              error={Boolean(profileErrors.full_name)}
              helperText={profileErrors.full_name?.message}
              sx={inputFieldSx}
            />
            <ValidatedTextField
              label="Телефон"
              fieldName="phone"
              registration={registerProfile('phone')}
              error={Boolean(profileErrors.phone)}
              helperText={profileErrors.phone?.message}
              sx={inputFieldSx}
            />
            <ValidatedTextField
              label="Электронная почта"
              fieldName="mail"
              registration={registerProfile('mail')}
              error={Boolean(profileErrors.mail)}
              helperText={profileErrors.mail?.message}
              sx={inputFieldSx}
            />
            <Button type="submit" variant="contained" fullWidth sx={submitButtonSx} disabled={isSubmittingProfile}>
              Сохранить изменения
            </Button>
          </Stack>
        </DialogContent>
      </Dialog>

      <Dialog open={openCompany} onClose={() => setOpenCompany(false)} fullWidth maxWidth="sm" PaperProps={{ sx: dialogPaperSx }}>
        <DialogContent sx={dialogContentSx}>
          <Stack spacing={2} component="form" onSubmit={handleCompanySubmit((values) => void onSubmitCompany(values))}>
            <Typography variant="h5" fontWeight={600} lineHeight={1}>
              Юридические данные компании
            </Typography>
            <ValidatedTextField
              label="ИНН"
              fieldName="inn"
              registration={registerCompany('inn')}
              error={Boolean(companyErrors.inn)}
              helperText={companyErrors.inn?.message}
              sx={inputFieldSx}
            />
            <ValidatedTextField
              label="Наименование"
              fieldName="company_name"
              registration={registerCompany('company_name')}
              error={Boolean(companyErrors.company_name)}
              helperText={companyErrors.company_name?.message}
              sx={inputFieldSx}
            />
            <ValidatedTextField
              label="Телефон"
              fieldName="company_phone"
              registration={registerCompany('company_phone')}
              error={Boolean(companyErrors.company_phone)}
              helperText={companyErrors.company_phone?.message}
              sx={inputFieldSx}
            />
            <ValidatedTextField
              label="Электронная почта"
              fieldName="company_mail"
              registration={registerCompany('company_mail')}
              error={Boolean(companyErrors.company_mail)}
              helperText={companyErrors.company_mail?.message}
              sx={inputFieldSx}
            />
            <ValidatedTextField
              label="Адрес"
              fieldName="address"
              registration={registerCompany('address')}
              error={Boolean(companyErrors.address)}
              helperText={companyErrors.address?.message}
              sx={inputFieldSx}
            />
            <ValidatedTextField
              label="Дополнительная информация"
              fieldName="note"
              multiline
              minRows={3}
              registration={registerCompany('note')}
              error={Boolean(companyErrors.note)}
              helperText={companyErrors.note?.message}
              sx={inputFieldSx}
            />
            <Button type="submit" variant="contained" fullWidth sx={submitButtonSx} disabled={isSubmittingCompany}>
              Сохранить изменения
            </Button>
          </Stack>
        </DialogContent>
      </Dialog>
    </>
  );
};
