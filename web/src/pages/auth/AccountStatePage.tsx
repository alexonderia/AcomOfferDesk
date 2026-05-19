import { Alert, Box, Button, CircularProgress, Paper, Stack, TextField, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import {
  getCurrentUserProfile,
  updateMyCompanyContacts,
  updateMyProfile,
  type CurrentUserProfile
} from '@shared/api/users/getCurrentUserProfile';
import { ROLE } from '@shared/constants/roles';
import { formatRuPhone, isValidRuPhone } from '@shared/lib/phone';
import { getDefaultPathByRole } from '@shared/lib/routing/getDefaultPathByRole';
import { useSystemToasts } from '@shared/ui/toasts';

type ProfileDraft = {
  fullName: string;
  phone: string;
  mail: string;
  companyName: string;
  inn: string;
  companyPhone: string;
  companyMail: string;
  address: string;
  note: string;
};

type DraftErrors = Partial<Record<keyof ProfileDraft, string>>;

type StatusContent = {
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'error';
};

const emptyDraft: ProfileDraft = {
  fullName: '',
  phone: '',
  mail: '',
  companyName: '',
  inn: '',
  companyPhone: '',
  companyMail: '',
  address: '',
  note: ''
};

const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const innRegex = /^\d{10}$|^\d{12}$/;

const normalizeDraftValue = (value: string | null | undefined) => {
  const normalized = (value ?? '').trim();
  if (!normalized) {
    return '';
  }
  if (['РЅРµ СѓРєР°Р·Р°РЅРѕ', 'none', 'null'].includes(normalized.toLowerCase())) {
    return '';
  }
  return normalized;
};

const buildDraft = (profile: CurrentUserProfile | null): ProfileDraft => ({
  fullName: normalizeDraftValue(profile?.fullName),
  phone: formatRuPhone(normalizeDraftValue(profile?.phone)),
  mail: normalizeDraftValue(profile?.mail),
  companyName: normalizeDraftValue(profile?.company.companyName),
  inn: normalizeDraftValue(profile?.company.inn),
  companyPhone: formatRuPhone(normalizeDraftValue(profile?.company.phone)),
  companyMail: normalizeDraftValue(profile?.company.mail),
  address: normalizeDraftValue(profile?.company.address),
  note: normalizeDraftValue(profile?.company.note)
});

const getStatusContent = (status: string): StatusContent => {
  if (status === 'review') {
    return {
      title: 'РџСЂРѕРІРµСЂСЏРµРј РґР°РЅРЅС‹Рµ',
      description: 'Р—Р°РїРѕР»РЅРёС‚Рµ Р»РёС‡РЅС‹Рµ РґР°РЅРЅС‹Рµ Рё РґР°РЅРЅС‹Рµ РєРѕРјРїР°РЅРёРё. РџРѕСЃР»Рµ РїСЂРѕРІРµСЂРєРё РјС‹ СѓРІРµРґРѕРјРёРј Рѕ РІС‹РґР°С‡Рµ РґРѕСЃС‚СѓРїР° РїРѕ СЌР»РµРєС‚СЂРѕРЅРЅРѕР№ РїРѕС‡С‚Рµ.',
      severity: 'info'
    };
  }
  if (status === 'inactive') {
    return {
      title: 'Р”РѕСЃС‚СѓРї РІСЂРµРјРµРЅРЅРѕ РѕС‚РєР»СЋС‡С‘РЅ',
      description: 'РћР±СЂР°С‚РёС‚РµСЃСЊ Рє Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂСѓ РїСЂРѕРµРєС‚Р°.',
      severity: 'warning'
    };
  }
  if (status === 'blacklist') {
    return {
      title: 'Р”РѕСЃС‚СѓРї Р·Р°РєСЂС‹С‚',
      description: 'Р”Р»СЏ СѓС‚РѕС‡РЅРµРЅРёСЏ РґРµС‚Р°Р»РµР№ СЃРІСЏР¶РёС‚РµСЃСЊ СЃ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂРѕРј РїСЂРѕРµРєС‚Р°.',
      severity: 'error'
    };
  }
  return {
    title: 'РћР¶РёРґР°Р№С‚Рµ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ',
    description: 'РњС‹ СѓРІРµРґРѕРјРёРј РІР°СЃ, РєРѕРіРґР° РґРѕСЃС‚СѓРї Р±СѓРґРµС‚ РѕС‚РєСЂС‹С‚.',
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
    errors.fullName = 'РЈРєР°Р¶РёС‚Рµ Р¤РРћ';
  } else if (fullName.length > 256) {
    errors.fullName = 'РњР°РєСЃРёРјСѓРј 256 СЃРёРјРІРѕР»РѕРІ';
  }

  if (!phone) {
    errors.phone = 'РЈРєР°Р¶РёС‚Рµ С‚РµР»РµС„РѕРЅ';
  } else if (!isValidRuPhone(phone)) {
    errors.phone = 'РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ С„РѕСЂРјР°С‚ С‚РµР»РµС„РѕРЅР°';
  }

  if (mail) {
    if (mail.length > 256) {
      errors.mail = 'РњР°РєСЃРёРјСѓРј 256 СЃРёРјРІРѕР»РѕРІ';
    } else if (!emailRegex.test(mail)) {
      errors.mail = 'РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ email';
    }
  }

  if (!requireCompany) {
    return errors;
  }

  if (!companyName) {
    errors.companyName = 'РЈРєР°Р¶РёС‚Рµ РЅР°РёРјРµРЅРѕРІР°РЅРёРµ РєРѕРјРїР°РЅРёРё';
  } else if (companyName.length > 256) {
    errors.companyName = 'РњР°РєСЃРёРјСѓРј 256 СЃРёРјРІРѕР»РѕРІ';
  }

  if (!inn) {
    errors.inn = 'РЈРєР°Р¶РёС‚Рµ РРќРќ';
  } else if (!innRegex.test(inn)) {
    errors.inn = 'РРќРќ РґРѕР»Р¶РµРЅ СЃРѕРґРµСЂР¶Р°С‚СЊ 10 РёР»Рё 12 С†РёС„СЂ';
  }

  if (!companyPhone) {
    errors.companyPhone = 'РЈРєР°Р¶РёС‚Рµ С‚РµР»РµС„РѕРЅ РєРѕРјРїР°РЅРёРё';
  } else if (!isValidRuPhone(companyPhone)) {
    errors.companyPhone = 'РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ С„РѕСЂРјР°С‚ С‚РµР»РµС„РѕРЅР°';
  }

  if (companyMail) {
    if (companyMail.length > 256) {
      errors.companyMail = 'РњР°РєСЃРёРјСѓРј 256 СЃРёРјРІРѕР»РѕРІ';
    } else if (!emailRegex.test(companyMail)) {
      errors.companyMail = 'РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ email';
    }
  }

  if (address.length > 256) {
    errors.address = 'РњР°РєСЃРёРјСѓРј 256 СЃРёРјРІРѕР»РѕРІ';
  }
  if (note.length > 1024) {
    errors.note = 'РњР°РєСЃРёРјСѓРј 1024 СЃРёРјРІРѕР»Р°';
  }

  return errors;
};

export const AccountStatePage = () => {
  const navigate = useNavigate();
  const { session, logout } = useAuth();
  const { showErrorToast, showSuccessToast } = useSystemToasts();
  const [draft, setDraft] = useState<ProfileDraft>(emptyDraft);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showValidation, setShowValidation] = useState(false);
  const [touchedFields, setTouchedFields] = useState<Partial<Record<keyof ProfileDraft, boolean>>>({});

  const isContractor = session?.roleId === ROLE.CONTRACTOR;
  const isReview = session?.status === 'review';
  const isBlocked = session?.status === 'inactive' || session?.status === 'blacklist';

  useEffect(() => {
    if (!session) {
      navigate('/login', { replace: true });
      return;
    }
    if (session.businessAccess) {
      navigate(getDefaultPathByRole(session.roleId), { replace: true });
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    void getCurrentUserProfile()
      .then((data) => {
        if (cancelled) {
          return;
        }
        setDraft(buildDraft(data));
        setTouchedFields({});
        setShowValidation(false);
      })
      .catch((error) => {
        if (!cancelled) {
          setErrorMessage(error instanceof Error ? error.message : 'РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ РґР°РЅРЅС‹Рµ.');
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
  }, [navigate, session]);

  const canEditCompany = useMemo(() => isContractor && isReview, [isContractor, isReview]);
  const statusContent = useMemo(() => getStatusContent(session?.status ?? ''), [session?.status]);
  const validationErrors = useMemo(
    () => validateDraft(draft, { requireCompany: canEditCompany }),
    [canEditCompany, draft]
  );

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
      setErrorMessage('РџСЂРѕРІРµСЂСЊС‚Рµ РєРѕСЂСЂРµРєС‚РЅРѕСЃС‚СЊ Р·Р°РїРѕР»РЅРµРЅРёСЏ РїРѕР»РµР№.');
      return;
    }

    setIsSaving(true);
    try {
      const nextProfile = await updateMyProfile({
        full_name: draft.fullName.trim(),
        phone: draft.phone.trim(),
        mail: draft.mail.trim() || undefined
      });
      if (canEditCompany) {
        const nextWithCompany = await updateMyCompanyContacts({
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
      showSuccessToast('Р”Р°РЅРЅС‹Рµ РїРµСЂРµРґР°РЅС‹ РЅР° РїСЂРѕРІРµСЂРєСѓ. РњС‹ СѓРІРµРґРѕРјРёРј РІР°СЃ Рѕ РІС‹РґР°С‡Рµ РґРѕСЃС‚СѓРїР° РїРѕ СЌР»РµРєС‚СЂРѕРЅРЅРѕР№ РїРѕС‡С‚Рµ.');
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
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
      <Paper sx={{ p: 4, width: { xs: '100%', sm: 720 } }}>
        {isLoading ? (
          <Stack alignItems="center" spacing={2}>
            <CircularProgress size={28} />
            <Typography variant="body2" color="text.secondary">
              Р—Р°РіСЂСѓР¶Р°РµРј РґР°РЅРЅС‹Рµ.
            </Typography>
          </Stack>
        ) : (
          <Stack spacing={2.5}>
            <Stack spacing={0.5}>
              <Typography variant="h5" fontWeight={700}>
                {statusContent.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {statusContent.description}
              </Typography>
            </Stack>

            <Alert severity={statusContent.severity}>РЎС‚Р°С‚СѓСЃ: {statusContent.title.toLowerCase()}.</Alert>
            {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}

            {!isBlocked ? (
              <>
                <Stack spacing={1.5}>
                  <Typography variant="subtitle1" fontWeight={600}>Р›РёС‡РЅС‹Рµ РґР°РЅРЅС‹Рµ</Typography>
                  <TextField
                    label="Р¤РРћ"
                    value={draft.fullName}
                    onBlur={() => markFieldTouched('fullName')}
                    onChange={(event) => {
                      setDraft((prev) => ({ ...prev, fullName: event.target.value }));
                      markFieldTouched('fullName');
                    }}
                    error={shouldShowFieldError('fullName')}
                    helperText={getFieldHelperText('fullName')}
                  />
                  <TextField
                    label="РўРµР»РµС„РѕРЅ"
                    value={draft.phone}
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
                    <Typography variant="subtitle1" fontWeight={600}>Р”Р°РЅРЅС‹Рµ РєРѕРјРїР°РЅРёРё</Typography>
                    <TextField
                      label="РљРѕРјРїР°РЅРёСЏ"
                      value={draft.companyName}
                      onBlur={() => markFieldTouched('companyName')}
                      onChange={(event) => {
                        setDraft((prev) => ({ ...prev, companyName: event.target.value }));
                        markFieldTouched('companyName');
                      }}
                      error={shouldShowFieldError('companyName')}
                      helperText={getFieldHelperText('companyName')}
                    />
                    <TextField
                      label="РРќРќ"
                      value={draft.inn}
                      onBlur={() => markFieldTouched('inn')}
                      onChange={(event) => {
                        setDraft((prev) => ({ ...prev, inn: event.target.value.replace(/\D/g, '') }));
                        markFieldTouched('inn');
                      }}
                      error={shouldShowFieldError('inn')}
                      helperText={getFieldHelperText('inn')}
                    />
                    <TextField
                      label="РўРµР»РµС„РѕРЅ РєРѕРјРїР°РЅРёРё"
                      value={draft.companyPhone}
                      onBlur={() => markFieldTouched('companyPhone')}
                      onChange={(event) => {
                        setDraft((prev) => ({ ...prev, companyPhone: formatRuPhone(event.target.value) }));
                        markFieldTouched('companyPhone');
                      }}
                      error={shouldShowFieldError('companyPhone')}
                      helperText={getFieldHelperText('companyPhone')}
                    />
                    <TextField
                      label="E-mail РєРѕРјРїР°РЅРёРё"
                      value={draft.companyMail}
                      onBlur={() => markFieldTouched('companyMail')}
                      onChange={(event) => {
                        setDraft((prev) => ({ ...prev, companyMail: event.target.value }));
                        markFieldTouched('companyMail');
                      }}
                      error={shouldShowFieldError('companyMail')}
                      helperText={getFieldHelperText('companyMail')}
                    />
                    <TextField
                      label="РђРґСЂРµСЃ"
                      value={draft.address}
                      onBlur={() => markFieldTouched('address')}
                      onChange={(event) => {
                        setDraft((prev) => ({ ...prev, address: event.target.value }));
                        markFieldTouched('address');
                      }}
                      error={shouldShowFieldError('address')}
                      helperText={getFieldHelperText('address')}
                    />
                    <TextField
                      label="РџСЂРёРјРµС‡Р°РЅРёРµ"
                      value={draft.note}
                      multiline
                      minRows={3}
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
                  {isSaving ? 'РЎРѕС…СЂР°РЅСЏРµРј...' : 'РћС‚РїСЂР°РІРёС‚СЊ РґР°РЅРЅС‹Рµ'}
                </Button>
              </>
            ) : null}

            <Stack direction="row" spacing={1.5}>
              <Button variant="outlined" onClick={logout} sx={{ textTransform: 'none' }}>
                Р’С‹Р№С‚Рё
              </Button>
            </Stack>
          </Stack>
        )}
      </Paper>
    </Box>
  );
};


