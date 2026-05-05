import { zodResolver } from '@hookform/resolvers/zod';
import PersonOutlineRounded from '@mui/icons-material/PersonOutlineRounded';
import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogContent,
  Stack,
  TextField,
  Tooltip,
  Typography
} from '@mui/material';
import { alpha, type Theme, useTheme } from '@mui/material/styles';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { useAuth } from '@app/providers/AuthProvider';
import { UnavailabilityManagementSection, UnavailabilityPeriodEditor } from '@entities/unavailability';
import {
  getCurrentUserProfile,
  setMyUnavailabilityPeriod,
  updateMyCompanyContacts,
  updateMyCredentials,
  updateMyProfile
} from '@shared/api/users/getCurrentUserProfile';
import type { CurrentUserProfile } from '@shared/api/users/getCurrentUserProfile';
import { ROLE } from '@shared/constants/roles';
import { requestEmailVerification } from '@shared/api/auth/emailVerification';
import { ActionButton } from '@shared/components/ActionButton';


const fallbackText = 'Не указано';

const dialogPaperSx = (theme: Theme) => ({
  borderRadius: 2,
  px: { xs: 2.5, sm: 3.5 },
  py: { xs: 3, sm: 3.5 },
  backgroundColor: theme.palette.background.default,
  maxHeight: 'min(760px, calc(100vh - 32px))',
  overflow: 'hidden',
  boxShadow: `0 24px 80px ${alpha(theme.palette.common.black, 0.18)}`
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

const defaultDbPlaceholder = 'не указано';

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

// profiles: full_name и phone обязательные, mail имеет default в БД
const profileSchema = z.object({
  full_name: z.string().trim().min(1, 'Введите ФИО'),
  phone: z.string().trim().min(1, 'Введите телефон'),
  mail: optionalEmail
});

// company_contacts: company_name, inn, phone обязательные,
// mail/address/note имеют default в БД
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
type CompanyFormValues = z.infer<typeof companySchema>;
type UnavailabilityFormValues = z.infer<typeof unavailabilitySchema>;

const DataRow = ({ label, value }: { label: string; value: string | null }) => (
  <Stack direction="row" spacing={2}>
    <Typography sx={{ width: 170, color: 'text.primary' }}>{label}</Typography>
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

type ProfileButtonProps = {
  iconOnly?: boolean;
  sidebar?: boolean;
};

export const ProfileButton = ({ iconOnly = false, sidebar = false }: ProfileButtonProps) => {
  const theme = useTheme();
  const { session } = useAuth();
  const [open, setOpen] = useState(false);
  const [openPassword, setOpenPassword] = useState(false);
  const [openProfile, setOpenProfile] = useState(false);
  const [openCompany, setOpenCompany] = useState(false);
  const [openUnavailability, setOpenUnavailability] = useState(false);
  const [profile, setProfile] = useState<CurrentUserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const {
    register: registerPassword,
    handleSubmit: handlePasswordSubmit,
    formState: { errors: passwordErrors, isSubmitting: isSubmittingPassword },
    reset: resetPassword
  } = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { oldPassword: '', password: '', confirmPassword: '' }
  });

  const {
    register: registerProfile,
    handleSubmit: handleProfileSubmit,
    formState: { errors: profileErrors, isSubmitting: isSubmittingProfile },
    reset: resetProfile
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { full_name: '', phone: '', mail: '' }
  });

  const {
    register: registerCompany,
    handleSubmit: handleCompanySubmit,
    formState: { errors: companyErrors, isSubmitting: isSubmittingCompany },
    reset: resetCompany
  } = useForm<CompanyFormValues>({
    resolver: zodResolver(companySchema),
    defaultValues: { inn: '', company_name: '', company_phone: '', company_mail: '', address: '', note: '' }
  });

  const {
    register: registerUnavailability,
    handleSubmit: handleUnavailabilitySubmit,
    watch: watchUnavailability,
    setValue: setUnavailabilityValue,
    formState: { errors: unavailabilityErrors, isSubmitting: isSubmittingUnavailability },
    reset: resetUnavailability
  } = useForm<UnavailabilityFormValues>({
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
  }, [profile, resetCompany, resetProfile, resetUnavailability]);

  const loadProfile = async () => {
    setIsLoading(true);
    setError(null);
    setInfo(null);
    try {
      const data = await getCurrentUserProfile();
      setProfile(data);
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
  const canEditCredentials = Boolean(profile?.actions.manage_credentials) && session?.authProvider === 'legacy';
  const canEditProfile = Boolean(profile?.actions.manage_own_profile);
  const canEditCompany = Boolean(profile?.actions.manage_company_contacts);
  const canSetUnavailability = Boolean(profile?.actions.manage_own_unavailability);

  const onSubmitPassword = async (values: PasswordFormValues) => {
    setError(null);
    setInfo(null);
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
    setInfo(null);
    try {
      const normalizedMail = normalizeOptional(values.mail);
      const currentMail = normalizeOptional(profile?.mail ?? '');
      const normalizedMailLower = normalizedMail?.toLowerCase();
      const currentMailLower = currentMail?.toLowerCase() ?? '';
      const shouldRequestVerification =
        Boolean(normalizedMailLower) &&
        normalizedMailLower !== currentMailLower;
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
        setInfo(verificationDetail);
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Не удалось обновить личные данные');
    }
  };

  const onSubmitCompany = async (values: CompanyFormValues) => {
    setError(null);
    setInfo(null);
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

  const onSubmitUnavailability = async (values: UnavailabilityFormValues) => {
    setError(null);
    setInfo(null);
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
                {'Профиль'}
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

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: dialogPaperSx
        }}
      >
        <DialogContent sx={dialogContentSx}>
          {isLoading ? (
            <Stack alignItems="center" justifyContent="center" sx={{ minHeight: 240 }}>
              <CircularProgress size={28} />
            </Stack>
          ) : (
            <Stack spacing={2}>
              {error ? <Alert severity="error">{error}</Alert> : null}
              {info ? <Alert severity="info">{info}</Alert> : null}
              
              <Stack spacing={1.5}>
                <Typography variant="h5" fontWeight={600} lineHeight={1}>
                  Личные данные
                </Typography>
                <DataRow label="Логин" value={session?.login ?? profile?.userId ?? null} />
                <DataRow label="ФИО" value={profile?.fullName ?? null} />
                <DataRow label="Телефон" value={profile?.phone ?? null} />
                <DataRow label="E-mail" value={profile?.mail ?? null} />
              </Stack>

              <Stack spacing={1.25}>
                {canEditCredentials ? (
                  <Button variant="outlined" sx={{ borderRadius: 1, textTransform: 'none' }} onClick={() => setOpenPassword(true)}>
                    Изменить данные входа
                  </Button>
                ) : null}
                {canEditProfile ? (
                  <Button variant="outlined" sx={{ borderRadius: 1, textTransform: 'none' }} onClick={() => setOpenProfile(true)}>
                    Изменить данные для связи
                  </Button>
                ) : null}
              </Stack>

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
                  <Typography variant="h5" fontWeight={600} lineHeight={1}>
                    Данные компании
                  </Typography>
                  <Box
                    sx={{
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 2,
                      p: 1.5,
                      backgroundColor: 'rgba(255,255,255,0.24)'
                    }}
                  >
                    <DataRow label="ИНН" value={profile?.company.inn ?? null} />
                    <DataRow label="Наименование" value={profile?.company.companyName ?? null} />
                    <DataRow label="Телефон" value={profile?.company.phone ?? null} />
                    <DataRow label="E-mail" value={profile?.company.mail ?? null} />
                    <DataRow label="Адрес" value={profile?.company.address ?? null} />
                    <DataRow label="Доп. информация" value={profile?.company.note ?? null} />
                  </Box>
                  {canEditCompany ? (
                    <Button variant="outlined" sx={{ borderRadius: 1, textTransform: 'none' }} onClick={() => setOpenCompany(true)}>
                      Изменить данные компании
                    </Button>
                  ) : null}
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
            <TextField
              label="Старый пароль"
              type="password"
              {...registerPassword('oldPassword')}
              error={Boolean(passwordErrors.oldPassword)}
              helperText={passwordErrors.oldPassword?.message}
              sx={inputFieldSx}
            />
            <TextField
              label="Новый пароль"
              type="password"
              {...registerPassword('password')}
              error={Boolean(passwordErrors.password)}
              helperText={passwordErrors.password?.message}
              sx={inputFieldSx}
            />
            <TextField
              label="Повторите новый пароль"
              type="password"
              {...registerPassword('confirmPassword')}
              error={Boolean(passwordErrors.confirmPassword)}
              helperText={passwordErrors.confirmPassword?.message}
              sx={inputFieldSx}
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              sx={{ borderRadius: 1, textTransform: 'none', py: 1.25, fontSize: 16, fontWeight: 700, boxShadow: 'none' }}
              disabled={isSubmittingPassword}
            >
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
            <TextField
              label="ФИО"
              {...registerProfile('full_name')}
              error={Boolean(profileErrors.full_name)}
              helperText={profileErrors.full_name?.message}
              sx={inputFieldSx}
            />
            <TextField
              label="Телефон"
              {...registerProfile('phone')}
              error={Boolean(profileErrors.phone)}
              helperText={profileErrors.phone?.message}
              sx={inputFieldSx}
            />
            <TextField
              label="Электронная почта"
              {...registerProfile('mail')}
              error={Boolean(profileErrors.mail)}
              helperText={profileErrors.mail?.message}
              sx={inputFieldSx}
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              sx={{ borderRadius: 1, textTransform: 'none', py: 1.25, fontSize: 16, fontWeight: 700, boxShadow: 'none' }}
              disabled={isSubmittingProfile}
            >
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
            <TextField
              label="ИНН"
              {...registerCompany('inn')}
              error={Boolean(companyErrors.inn)}
              helperText={companyErrors.inn?.message}
              sx={inputFieldSx}
            />
            <TextField
              label="Наименование"
              {...registerCompany('company_name')}
              error={Boolean(companyErrors.company_name)}
              helperText={companyErrors.company_name?.message}
              sx={inputFieldSx}
            />
            <TextField
              label="Телефон"
              {...registerCompany('company_phone')}
              error={Boolean(companyErrors.company_phone)}
              helperText={companyErrors.company_phone?.message}
              sx={inputFieldSx}
            />
            <TextField
              label="Электронная почта"
              {...registerCompany('company_mail')}
              error={Boolean(companyErrors.company_mail)}
              helperText={companyErrors.company_mail?.message}
              sx={inputFieldSx}
            />
            <TextField
              label="Адрес"
              {...registerCompany('address')}
              error={Boolean(companyErrors.address)}
              helperText={companyErrors.address?.message}
              sx={inputFieldSx}
            />
            <TextField
              label="Дополнительная информация"
              multiline
              minRows={3}
              {...registerCompany('note')}
              error={Boolean(companyErrors.note)}
              helperText={companyErrors.note?.message}
              sx={inputFieldSx}
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              sx={{ borderRadius: 1, textTransform: 'none', py: 1.25, fontSize: 16, fontWeight: 700, boxShadow: 'none' }}
              disabled={isSubmittingCompany}
            >
              Сохранить изменения
            </Button>
          </Stack>
        </DialogContent>
      </Dialog>
    </>
  );
};
