import { zodResolver } from '@hookform/resolvers/zod';
import {
  Alert,
  Box,
  Button,
  ButtonBase,
  Collapse,
  Dialog,
  DialogContent,
  Divider,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography
} from '@mui/material';
import ExpandMoreRounded from '@mui/icons-material/ExpandMoreRounded';
import { alpha, useTheme } from '@mui/material/styles';
import { MouseEvent as ReactMouseEvent, useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import type { UserListItem } from '@entities/user';
import { UnavailabilityManagementSection, UnavailabilityPeriodEditor, hasPeriodOverlapByDate } from '@entities/unavailability';
import { updateUserStatus } from '@shared/api/users/updateUserStatus';
import { updateUserManager } from '@shared/api/users/updateUserManager';
import { updateUserRole } from '@shared/api/users/updateUserRole';
import { updateManualContractor } from '@shared/api/users/updateManualContractor';
import { getManagerCandidates } from '@shared/api/users/getManagerCandidates';
import { TableTemplate, type TableTemplateColumn } from '@shared/components/TableTemplate';
import { formatRuPhone, isValidRuPhone } from '@shared/lib/phone';
import { StatusPill as BaseStatusPill } from '@shared/ui/StatusPill';
import {
  UserStatusPill,
  InfoRow,
  SourceSection,
  dialogPaperSx,
  dialogContentSx,
  normalizeUserStatus,
  userStatusLabelByValue,
} from './UserCardPrimitives';
import {
  getSubordinateProfile,
  setSubordinateUnavailabilityPeriod,
  type SubordinateProfile
} from '@shared/api/users/getSubordinateProfile';

const statusSchema = z.object({
  user_status: z.enum(['review', 'active', 'inactive', 'blacklist'])
});

type StatusFormValues = z.infer<typeof statusSchema>;

const subordinateUnavailabilitySchema = z
  .object({
    status: z.enum(['sick', 'vacation', 'fired', 'maternity', 'business_trip', 'unavailable']),
    started_at: z.string().min(1, 'Выберите дату начала'),
    ended_at: z.string().min(1, 'Выберите дату окончания')
  })
  .refine((values) => new Date(values.ended_at).getTime() >= new Date(values.started_at).getTime(), {
    message: 'Дата окончания должна быть не раньше даты начала',
    path: ['ended_at']
  });

type SubordinateUnavailabilityFormValues = z.infer<typeof subordinateUnavailabilitySchema>;

type UsersTableProps = {
  users: UserListItem[];
  isLoading?: boolean;
  emptyMessage: string;
  onAddClick?: () => void;
  getRoleLabel: (roleId: number) => string;
  isContractorsTab: boolean;
  canViewRoleIds: boolean;
  canUpdateStatus: boolean;
  canUpdateRole: boolean;
  allowedRoleOptions: number[];
  onStatusUpdated: () => Promise<void>;
};

type UserRow = {
  id: string;
  full_name: string;
  phone: string;
  mail: string;
  id_role: number;
  role: string;
  status: StatusFormValues['user_status'];
};

const tgStatusLabelByValue: Record<'review' | 'approved' | 'disapproved', string> = {
  review: 'На проверке',
  approved: 'Одобрен',
  disapproved: 'Не одобрен'
};

const userStatusValueByLabel: Record<string, StatusFormValues['user_status']> = {
  'на проверке': 'review',
  'активен': 'active',
  'неактивен': 'inactive',
  'в черном списке': 'blacklist',
  'в чёрном списке': 'blacklist'
};

const tgStatusValueByLabel: Record<string, 'review' | 'approved' | 'disapproved'> = {
  'на проверке': 'review',
  'одобрен': 'approved',
  'не одобрен': 'disapproved'
};

const normalizeAnyStatus = (value: string | null | undefined): string => {
  const normalized = (value ?? '').toLowerCase();
  if (normalized in userStatusLabelByValue) {
    return normalized;
  }
  if (normalized in userStatusValueByLabel) {
    return userStatusValueByLabel[normalized];
  }
  if (normalized in tgStatusValueByLabel) {
    return tgStatusValueByLabel[normalized];
  }
  return normalized;
};

const toStatusLabel = (value: string | null | undefined): string => {
  const normalized = normalizeAnyStatus(value);
  if (normalized in userStatusLabelByValue) {
    return userStatusLabelByValue[normalized as StatusFormValues['user_status']];
  }
  if (normalized in tgStatusLabelByValue) {
    return tgStatusLabelByValue[normalized as 'review' | 'approved' | 'disapproved'];
  }
  return value ?? '—';
};

const contractorStatusToneByValue: Record<string, 'success' | 'warning' | 'error' | 'info' | 'neutral'> = {
  review: 'warning',
  active: 'success',
  inactive: 'neutral',
  blacklist: 'error',
  approved: 'success',
  disapproved: 'error'
};

const ContractorStatusPill = ({ value }: { value: string | null | undefined }) => (
  <BaseStatusPill label={toStatusLabel(value)} tone={contractorStatusToneByValue[normalizeAnyStatus(value)] ?? 'info'} />
);

const formatPhoneForView = (value: string | null | undefined) => {
  if (!value) {
    return null;
  }
  const formatted = formatRuPhone(value);
  return formatted || value;
};

type UserMobileCardProps = {
  row: UserRow;
  canViewRoleIds: boolean;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onOpenDetails?: (row: UserRow) => void;
};

const UserMobileCard = ({ row, canViewRoleIds, isExpanded, onToggleExpand, onOpenDetails }: UserMobileCardProps) => {
  const theme = useTheme();
  const detailRows = [
    { key: 'login', label: 'Логин', value: row.id },
    { key: 'full_name', label: 'ФИО', value: row.full_name },
    { key: 'phone', label: 'Телефон', value: row.phone },
    { key: 'mail', label: 'E-mail', value: row.mail },
    ...(canViewRoleIds ? [{ key: 'role_id', label: 'ID роли', value: String(row.id_role) }] : []),
    { key: 'role', label: 'Роль', value: row.role },
    { key: 'status', label: 'Статус профиля', value: userStatusLabelByValue[row.status] }
  ];

  const handleToggleExpand = (event: ReactMouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    onToggleExpand();
  };

  return (
    <Paper
      onClick={onOpenDetails ? () => onOpenDetails(row) : undefined}
      sx={{
        p: { xs: 1.25, sm: 1.5 },
        borderRadius: `${theme.acomShape.controlRadius}px`,
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
        cursor: onOpenDetails ? 'pointer' : 'default',
        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
        boxShadow: `0 2px 8px ${alpha(theme.palette.common.black, 0.04)}`,
        '&:hover': {
          borderColor: 'primary.main',
          boxShadow: `0 6px 14px ${alpha(theme.palette.common.black, 0.08)}`
        }
      }}
    >
      <Stack spacing={1.05}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" gap={1}>
          <Stack sx={{ minWidth: 0, gap: 0.35 }}>
            <Typography
              sx={{
                minWidth: 0,
                fontSize: 16,
                fontWeight: 600,
                color: 'text.primary',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}
            >
              {row.id}
            </Typography>
            <Typography
              sx={{
                fontSize: 14,
                lineHeight: 1.35,
                color: 'text.secondary',
                display: '-webkit-box',
                WebkitBoxOrient: 'vertical',
                WebkitLineClamp: 2,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'normal',
                wordBreak: 'break-word'
              }}
            >
              {row.full_name}
            </Typography>
          </Stack>
          <UserStatusPill value={row.status} />
        </Stack>

        <Divider />

        <Stack spacing={0}>
          <ButtonBase
            onClick={handleToggleExpand}
            sx={{
              width: '100%',
              px: 0.2,
              py: 0.55,
              borderRadius: `${theme.acomShape.controlRadius}px`,
              justifyContent: 'space-between',
              color: 'inherit',
              transition: 'background-color 0.2s ease',
              '&:hover': {
                bgcolor: alpha(theme.palette.primary.main, 0.06)
              }
            }}
          >
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ width: '100%' }}>
              <Typography
                sx={{
                  fontSize: 12,
                  lineHeight: 1.25,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: 0.3,
                  color: 'primary.main'
                }}
              >
                Детали пользователя
              </Typography>
              <ExpandMoreRounded
                sx={{
                  fontSize: 20,
                  color: 'primary.main',
                  transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.28s ease'
                }}
              />
            </Stack>
          </ButtonBase>

          <Collapse in={isExpanded} timeout={{ enter: 300, exit: 220 }} unmountOnExit>
            <Stack divider={<Divider flexItem />} spacing={0}>
              {detailRows.map((detail) => (
                <Stack key={`${row.id}-${detail.key}`} sx={{ py: 0.72 }}>
                  <Stack direction="row" alignItems="flex-start" gap={1.15} sx={{ minWidth: 0 }}>
                    <Typography
                      sx={{
                        minWidth: 0,
                        flex: '0 0 44%',
                        fontSize: 11,
                        fontWeight: 600,
                        color: 'text.secondary',
                        textTransform: 'uppercase',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {detail.label}
                    </Typography>
                    <Typography
                      sx={{
                        minWidth: 0,
                        flex: 1,
                        fontSize: 15,
                        lineHeight: 1.3,
                        fontWeight: 500,
                        color: detail.value === '—' ? 'text.secondary' : 'text.primary',
                        whiteSpace: 'normal',
                        wordBreak: 'break-word'
                      }}
                    >
                      {detail.value}
                    </Typography>
                  </Stack>
                </Stack>
              ))}
            </Stack>
          </Collapse>
        </Stack>
      </Stack>
    </Paper>
  );
};

type ContractorMobileCardProps = {
  row: UserListItem;
  isContactExpanded: boolean;
  isCompanyExpanded: boolean;
  onToggleContact: () => void;
  onToggleCompany: () => void;
  onOpenDetails?: (row: UserListItem) => void;
};

const ContractorMobileCard = ({
  row,
  isContactExpanded,
  isCompanyExpanded,
  onToggleContact,
  onToggleCompany,
  onOpenDetails
}: ContractorMobileCardProps) => {
  const theme = useTheme();
  const name = row.full_name?.trim();
  const title = name ? `${name} (${row.user_id})` : row.user_id;
  const contactRows = [
    { key: 'phone', label: 'Телефон', value: formatPhoneForView(row.phone) ?? '—' },
    { key: 'mail', label: 'Почта', value: row.mail ?? '—' }
  ];
  const companyRows = [
    { key: 'company_phone', label: 'Телефон', value: formatPhoneForView(row.company_phone) ?? '—' },
    { key: 'company_mail', label: 'Почта', value: row.company_mail ?? '—' },
    { key: 'company_name', label: 'Компания', value: row.company_name ?? '—' },
    { key: 'inn', label: 'ИНН', value: row.inn ?? '—' },
    { key: 'address', label: 'Адрес', value: row.address ?? '—' },
    { key: 'note', label: 'Примечание', value: row.note ?? '—' }
  ];

  const handleToggleContact = (event: ReactMouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    onToggleContact();
  };

  const handleToggleCompany = (event: ReactMouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    onToggleCompany();
  };

  return (
    <Paper
      onClick={onOpenDetails ? () => onOpenDetails(row) : undefined}
      sx={{
        p: { xs: 1.25, sm: 1.5 },
        borderRadius: `${theme.acomShape.controlRadius}px`,
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
        cursor: onOpenDetails ? 'pointer' : 'default',
        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
        boxShadow: `0 2px 8px ${alpha(theme.palette.common.black, 0.04)}`,
        '&:hover': {
          borderColor: 'primary.main',
          boxShadow: `0 6px 14px ${alpha(theme.palette.common.black, 0.08)}`
        }
      }}
    >
      <Stack spacing={1.05}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" gap={1}>
          <Typography
            sx={{
              minWidth: 0,
              fontSize: 16,
              fontWeight: 600,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              color: 'text.primary'
            }}
          >
            {title}
          </Typography>
          <ContractorStatusPill value={row.status} />
        </Stack>

        <Divider />

        <Stack spacing={0}>
          <ButtonBase
            onClick={handleToggleContact}
            sx={{
              width: '100%',
              px: 0.2,
              py: 0.55,
              borderRadius: `${theme.acomShape.controlRadius}px`,
              justifyContent: 'space-between',
              color: 'inherit',
              transition: 'background-color 0.2s ease',
              '&:hover': {
                bgcolor: alpha(theme.palette.primary.main, 0.06)
              }
            }}
          >
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ width: '100%' }}>
              <Typography
                sx={{
                  fontSize: 12,
                  lineHeight: 1.25,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: 0.3,
                  color: 'primary.main'
                }}
              >
                Для связи
              </Typography>
              <ExpandMoreRounded
                sx={{
                  fontSize: 20,
                  color: 'primary.main',
                  transform: isContactExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.28s ease'
                }}
              />
            </Stack>
          </ButtonBase>

          <Collapse in={isContactExpanded} timeout={{ enter: 300, exit: 220 }} unmountOnExit>
            <Stack divider={<Divider flexItem />} spacing={0}>
              {contactRows.map((detail) => (
                <Stack key={`${row.user_id}-${detail.key}`} sx={{ py: 0.72 }}>
                  <Stack direction="row" alignItems="flex-start" gap={1.15} sx={{ minWidth: 0 }}>
                    <Typography
                      sx={{
                        minWidth: 0,
                        flex: '0 0 44%',
                        fontSize: 11,
                        fontWeight: 600,
                        color: 'text.secondary',
                        textTransform: 'uppercase',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {detail.label}
                    </Typography>
                    <Typography
                      sx={{
                        minWidth: 0,
                        flex: 1,
                        fontSize: 15,
                        lineHeight: 1.3,
                        fontWeight: 500,
                        color: detail.value === '—' ? 'text.secondary' : 'text.primary',
                        whiteSpace: 'normal',
                        wordBreak: 'break-word'
                      }}
                    >
                      {detail.value}
                    </Typography>
                  </Stack>
                </Stack>
              ))}
            </Stack>
          </Collapse>
        </Stack>

        <Divider />

        <Stack spacing={0}>
          <ButtonBase
            onClick={handleToggleCompany}
            sx={{
              width: '100%',
              px: 0.2,
              py: 0.55,
              borderRadius: `${theme.acomShape.controlRadius}px`,
              justifyContent: 'space-between',
              color: 'inherit',
              transition: 'background-color 0.2s ease',
              '&:hover': {
                bgcolor: alpha(theme.palette.primary.main, 0.06)
              }
            }}
          >
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ width: '100%' }}>
              <Typography
                sx={{
                  fontSize: 12,
                  lineHeight: 1.25,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: 0.3,
                  color: 'primary.main'
                }}
              >
                Компания
              </Typography>
              <ExpandMoreRounded
                sx={{
                  fontSize: 20,
                  color: 'primary.main',
                  transform: isCompanyExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.28s ease'
                }}
              />
            </Stack>
          </ButtonBase>

          <Collapse in={isCompanyExpanded} timeout={{ enter: 300, exit: 220 }} unmountOnExit>
            <Stack divider={<Divider flexItem />} spacing={0}>
              {companyRows.map((detail) => (
                <Stack key={`${row.user_id}-${detail.key}`} sx={{ py: 0.72 }}>
                  <Stack direction="row" alignItems="flex-start" gap={1.15} sx={{ minWidth: 0 }}>
                    <Typography
                      sx={{
                        minWidth: 0,
                        flex: '0 0 44%',
                        fontSize: 11,
                        fontWeight: 600,
                        color: 'text.secondary',
                        textTransform: 'uppercase',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {detail.label}
                    </Typography>
                    <Typography
                      sx={{
                        minWidth: 0,
                        flex: 1,
                        fontSize: 15,
                        lineHeight: 1.3,
                        fontWeight: 500,
                        color: detail.value === '—' ? 'text.secondary' : 'text.primary',
                        whiteSpace: 'normal',
                        wordBreak: 'break-word'
                      }}
                    >
                      {detail.value}
                    </Typography>
                  </Stack>
                </Stack>
              ))}
            </Stack>
          </Collapse>
        </Stack>
      </Stack>
    </Paper>
  );
};

type ManualContractorDraft = {
  login: string;
  full_name: string;
  phone: string;
  mail: string;
  company_name: string;
  inn: string;
  company_phone: string;
  company_mail: string;
  address: string;
  note: string;
};

type ManualContractorField = keyof ManualContractorDraft | 'password';
type ManualContractorFieldErrors = Partial<Record<ManualContractorField, string>>;

const buildManualContractorDraft = (user: UserListItem): ManualContractorDraft => ({
  login: user.user_id,
  full_name: user.full_name ?? '',
  phone: formatPhoneForView(user.phone) ?? '',
  mail: user.mail ?? '',
  company_name: user.company_name ?? '',
  inn: user.inn ?? '',
  company_phone: formatPhoneForView(user.company_phone) ?? '',
  company_mail: user.company_mail ?? '',
  address: user.address ?? '',
  note: user.note ?? ''
});

const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const utf8ByteLength = (value: string) => new TextEncoder().encode(value).length;

const buildManualContractorPayload = (
  user: UserListItem,
  draft: ManualContractorDraft,
  password: string
) => {
  const trimmedDraft: ManualContractorDraft = {
    login: draft.login.trim(),
    full_name: draft.full_name.trim(),
    phone: draft.phone.trim(),
    mail: draft.mail.trim(),
    company_name: draft.company_name.trim(),
    inn: draft.inn.trim(),
    company_phone: draft.company_phone.trim(),
    company_mail: draft.company_mail.trim(),
    address: draft.address.trim(),
    note: draft.note.trim()
  };
  const trimmedPassword = password.trim();

  const payload = {
    ...(trimmedDraft.login !== user.user_id ? { login: trimmedDraft.login } : {}),
    ...(trimmedPassword ? { password: trimmedPassword } : {}),
    ...(trimmedDraft.full_name !== (user.full_name ?? '') ? { full_name: trimmedDraft.full_name } : {}),
    ...(trimmedDraft.phone !== (user.phone ?? '') ? { phone: trimmedDraft.phone } : {}),
    ...(trimmedDraft.mail !== (user.mail ?? '') ? { mail: trimmedDraft.mail } : {}),
    ...(trimmedDraft.company_name !== (user.company_name ?? '') ? { company_name: trimmedDraft.company_name } : {}),
    ...(trimmedDraft.inn !== (user.inn ?? '') ? { inn: trimmedDraft.inn } : {}),
    ...(trimmedDraft.company_phone !== (user.company_phone ?? '') ? { company_phone: trimmedDraft.company_phone } : {}),
    ...(trimmedDraft.company_mail !== (user.company_mail ?? '') ? { company_mail: trimmedDraft.company_mail } : {}),
    ...(trimmedDraft.address !== (user.address ?? '') ? { address: trimmedDraft.address } : {}),
    ...(trimmedDraft.note !== (user.note ?? '') ? { note: trimmedDraft.note } : {})
  } as Parameters<typeof updateManualContractor>[1];

  return { trimmedDraft, payload };
};

const validateManualContractorPayload = (
  payload: Parameters<typeof updateManualContractor>[1]
): { fieldErrors: ManualContractorFieldErrors; firstError: string | null } => {
  const fieldErrors: ManualContractorFieldErrors = {};

  const setFieldError = (field: ManualContractorField, message: string) => {
    if (!fieldErrors[field]) {
      fieldErrors[field] = message;
    }
  };

  for (const [key, value] of Object.entries(payload)) {
    if (typeof value === 'string' && !value.trim()) {
      setFieldError(key as ManualContractorField, 'Поле не может быть пустым');
    }
  }

  const loginValue = payload.login;
  if (loginValue !== undefined && (loginValue.length < 3 || loginValue.length > 128)) {
    setFieldError('login', 'Логин должен содержать от 3 до 128 символов');
  }

  const passwordValue = payload.password;
  if (
    passwordValue !== undefined
    && (passwordValue.length < 6 || passwordValue.length > 72 || utf8ByteLength(passwordValue) > 72)
  ) {
    setFieldError('password', 'Пароль должен содержать от 6 до 72 символов (не более 72 байт)');
  }

  const phoneValue = payload.phone;
  if (phoneValue !== undefined && !isValidRuPhone(phoneValue)) {
    setFieldError('phone', 'Некорректный формат телефона контакта');
  }

  const companyPhoneValue = payload.company_phone;
  if (companyPhoneValue !== undefined && !isValidRuPhone(companyPhoneValue)) {
    setFieldError('company_phone', 'Некорректный формат телефона компании');
  }

  const mailValue = payload.mail;
  if (mailValue !== undefined && !emailRegex.test(mailValue)) {
    setFieldError('mail', 'Некорректный формат e-mail контакта');
  }

  const companyMailValue = payload.company_mail;
  if (companyMailValue !== undefined && !emailRegex.test(companyMailValue)) {
    setFieldError('company_mail', 'Некорректный формат e-mail компании');
  }

  const innValue = payload.inn;
  if (innValue !== undefined && !/^\d{10}$|^\d{12}$/.test(innValue)) {
    setFieldError('inn', 'ИНН должен содержать 10 или 12 цифр');
  }

  if (payload.full_name !== undefined && payload.full_name.length > 256) {
    setFieldError('full_name', 'Максимальная длина ФИО — 256 символов');
  }
  if (phoneValue !== undefined && phoneValue.length > 64) {
    setFieldError('phone', 'Максимальная длина телефона — 64 символа');
  }
  if (mailValue !== undefined && mailValue.length > 256) {
    setFieldError('mail', 'Максимальная длина e-mail — 256 символов');
  }
  if (payload.company_name !== undefined && payload.company_name.length > 256) {
    setFieldError('company_name', 'Максимальная длина наименования — 256 символов');
  }
  if (innValue !== undefined && innValue.length > 32) {
    setFieldError('inn', 'Максимальная длина ИНН — 32 символа');
  }
  if (companyPhoneValue !== undefined && companyPhoneValue.length > 64) {
    setFieldError('company_phone', 'Максимальная длина телефона — 64 символа');
  }
  if (companyMailValue !== undefined && companyMailValue.length > 256) {
    setFieldError('company_mail', 'Максимальная длина e-mail — 256 символов');
  }
  if (payload.address !== undefined && payload.address.length > 256) {
    setFieldError('address', 'Максимальная длина адреса — 256 символов');
  }
  if (payload.note !== undefined && payload.note.length > 1024) {
    setFieldError('note', 'Максимальная длина примечания — 1024 символа');
  }

  const firstError = Object.values(fieldErrors)[0] ?? null;
  return { fieldErrors, firstError };
};

const inlineStatusOptions: Array<StatusFormValues['user_status']> = ['review', 'active', 'inactive', 'blacklist'];


const statusMemoText = `Статусы users:

1) review
   Пользователь на проверке, доступ не выдан.

2) active
   Пользователь активен, доступ разрешён.

3) inactive
   Пользователь деактивирован, доступ запрещён.

4) blacklist
   Пользователь в чёрном списке, доступ запрещён.`;


export const UsersTable = ({
  users,
  isLoading,
  emptyMessage,
  onAddClick,
  getRoleLabel,
  isContractorsTab,
  canViewRoleIds,
  canUpdateStatus,
  canUpdateRole,
  allowedRoleOptions,
  onStatusUpdated
}: UsersTableProps) => {
  const [selectedUser, setSelectedUser] = useState<UserListItem | null>(null);
  const [expandedUserCardsById, setExpandedUserCardsById] = useState<Record<string, boolean>>({});
  const [expandedContractorCardsById, setExpandedContractorCardsById] = useState<Record<string, { contact: boolean; company: boolean }>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [inlineStatusError, setInlineStatusError] = useState<string | null>(null);
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);
  const [inlineRoleError, setInlineRoleError] = useState<string | null>(null);
  const [subordinateProfile, setSubordinateProfile] = useState<SubordinateProfile | null>(null);
  const [subordinateError, setSubordinateError] = useState<string | null>(null);
  const [managerOptions, setManagerOptions] = useState<UserListItem[]>([]);
  const [managerError, setManagerError] = useState<string | null>(null);
  const [managerUserId, setManagerUserId] = useState('');
  const [isUpdatingManager, setIsUpdatingManager] = useState(false);
  const [openSubordinateUnavailability, setOpenSubordinateUnavailability] = useState(false);
  const [manualContractorDraft, setManualContractorDraft] = useState<ManualContractorDraft>(() => ({
    login: '',
    full_name: '',
    phone: '',
    mail: '',
    company_name: '',
    inn: '',
    company_phone: '',
    company_mail: '',
    address: '',
    note: ''
  }));
  const [manualContractorPassword, setManualContractorPassword] = useState('');
  const [manualContractorError, setManualContractorError] = useState<string | null>(null);
  const [manualContractorSuccess, setManualContractorSuccess] = useState<string | null>(null);
  const [isUpdatingManualContractor, setIsUpdatingManualContractor] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting }
  } = useForm<StatusFormValues>({
    resolver: zodResolver(statusSchema),
    defaultValues: {
      user_status: 'review'
    }
  });

  useEffect(() => {
    if (selectedUser) {
      reset({
        user_status: normalizeUserStatus(selectedUser.status)
      });
    }
  }, [reset, selectedUser]);

  const {
    register: registerSubordinateUnavailability,
    handleSubmit: handleSubordinateUnavailabilitySubmit,
    watch: watchSubordinateUnavailability,
    setValue: setSubordinateUnavailabilityValue,
    formState: { errors: subordinateUnavailabilityErrors, isSubmitting: isSubmittingSubordinateUnavailability },
    reset: resetSubordinateUnavailability
  } = useForm<SubordinateUnavailabilityFormValues>({
    resolver: zodResolver(subordinateUnavailabilitySchema),
    defaultValues: { status: 'unavailable', started_at: '', ended_at: '' }
  });

  useEffect(() => {
    if (!subordinateProfile) {
      return;
    }
    resetSubordinateUnavailability({
      status: 'unavailable',
      started_at: '',
      ended_at: ''
    });
  }, [subordinateProfile, resetSubordinateUnavailability]);

  useEffect(() => {
    setManagerUserId(selectedUser?.id_parent ?? '');
  }, [selectedUser?.id_parent]);

  useEffect(() => {
    if (!selectedUser) {
      return;
    }
    setManualContractorDraft(buildManualContractorDraft(selectedUser));
    setManualContractorPassword('');
    setManualContractorError(null);
    setManualContractorSuccess(null);
  }, [selectedUser]);

  const manualContractorValidation = useMemo(() => {
    if (!selectedUser || !selectedUser.actions.manage_manual_contractor) {
      return {
        hasChanges: false,
        payload: {} as Parameters<typeof updateManualContractor>[1],
        trimmedDraft: {
          login: '',
          full_name: '',
          phone: '',
          mail: '',
          company_name: '',
          inn: '',
          company_phone: '',
          company_mail: '',
          address: '',
          note: ''
        } as ManualContractorDraft,
        fieldErrors: {} as ManualContractorFieldErrors,
        firstError: null as string | null
      };
    }

    const { payload, trimmedDraft } = buildManualContractorPayload(
      selectedUser,
      manualContractorDraft,
      manualContractorPassword
    );
    const { fieldErrors, firstError } = validateManualContractorPayload(payload);

    return {
      hasChanges: Object.keys(payload).length > 0,
      payload,
      trimmedDraft,
      fieldErrors,
      firstError
    };
  }, [manualContractorDraft, manualContractorPassword, selectedUser]);

  const updateManualContractorField = <K extends keyof ManualContractorDraft>(
    field: K,
    value: ManualContractorDraft[K]
  ) => {
    setManualContractorError(null);
    setManualContractorSuccess(null);
    setManualContractorDraft((prev) => ({ ...prev, [field]: value }));
  };

  const handleManualContractorPasswordChange = (value: string) => {
    setManualContractorError(null);
    setManualContractorSuccess(null);
    setManualContractorPassword(value);
  };

  useEffect(() => {
    if (!selectedUser?.actions.update_manager) {
      setManagerOptions([]);
      return;
    }

    let isCancelled = false;
    setManagerError(null);
    void getManagerCandidates(selectedUser.role_id)
      .then((result) => {
        if (!isCancelled) {
          setManagerOptions(result.items);
        }
      })
      .catch((error) => {
        if (!isCancelled) {
          setManagerError(error instanceof Error ? error.message : 'Не удалось загрузить список руководителей');
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [selectedUser?.actions.update_manager, selectedUser?.role_id, selectedUser?.user_id]);

  const rows: UserRow[] = useMemo(
    () =>
      users.map((user) => ({
        id: user.user_id,
        full_name: user.full_name ?? '—',
        phone: formatPhoneForView(user.phone) ?? '—',
        mail: user.mail ?? '—',
        id_role: user.role_id,
        role: getRoleLabel(user.role_id),
        status: normalizeUserStatus(user.status)
      })),
    [getRoleLabel, users]
  );

  const canEditUserStatus = (userId: string) => {
    const user = users.find((item) => item.user_id === userId);
    if (!canUpdateStatus || !user || !user.actions.update_status) {
      return false;
    }
    return true;
  };

  const handleStatusSubmit = async (values: StatusFormValues) => {
    if (!selectedUser) return;
    setSubmitError(null);
    setSubmitSuccess(null);

    try {
      await updateUserStatus(selectedUser.user_id, {
        user_status: values.user_status
      });
      setSubmitSuccess('Статус успешно обновлён.');
      await onStatusUpdated();
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'Не удалось обновить статус');
    }
  };

  const handleInlineStatusChange = async (userId: string, nextStatus: StatusFormValues['user_status']) => {
    setInlineStatusError(null);
    setUpdatingUserId(userId);

    try {
      await updateUserStatus(userId, {
        user_status: nextStatus
      });
      await onStatusUpdated();
    } catch (error) {
      setInlineStatusError(error instanceof Error ? error.message : 'Не удалось обновить статус');
    } finally {
      setUpdatingUserId(null);
    }
  };

  const handleInlineRoleChange = async (userId: string, nextRoleId: number) => {
    setInlineRoleError(null);
    setUpdatingUserId(userId);

    try {
      await updateUserRole(userId, { role_id: nextRoleId });
      await onStatusUpdated();
    } catch (error) {
      setInlineRoleError(error instanceof Error ? error.message : 'Не удалось обновить роль');
    } finally {
      setUpdatingUserId(null);
    }
  };

  const handleManagerUpdate = async () => {
    if (!selectedUser || !managerUserId || managerUserId === selectedUser.id_parent) {
      return;
    }

    setManagerError(null);
    setIsUpdatingManager(true);
    try {
      await updateUserManager(selectedUser.user_id, { manager_user_id: managerUserId });
      await onStatusUpdated();
      setSelectedUser(null);
      setSubordinateProfile(null);
    } catch (error) {
      setManagerError(error instanceof Error ? error.message : 'Не удалось обновить руководителя');
    } finally {
      setIsUpdatingManager(false);
    }
  };

  const handleManualContractorSave = async () => {
    if (!selectedUser || !selectedUser.actions.manage_manual_contractor) {
      return;
    }

    if (!manualContractorValidation.hasChanges) {
      setManualContractorError('Изменений не обнаружено');
      setManualContractorSuccess(null);
      return;
    }

    if (manualContractorValidation.firstError) {
      setManualContractorError(manualContractorValidation.firstError);
      setManualContractorSuccess(null);
      return;
    }

    setIsUpdatingManualContractor(true);
    setManualContractorError(null);
    setManualContractorSuccess(null);

    try {
      await updateManualContractor(selectedUser.user_id, manualContractorValidation.payload);

      setManualContractorPassword('');
      setManualContractorSuccess('Данные контрагента обновлены');
      await onStatusUpdated();
      setSelectedUser((prev) => (
        prev
          ? {
            ...prev,
            ...manualContractorValidation.trimmedDraft,
            user_id: manualContractorValidation.trimmedDraft.login
          }
          : prev
      ));
    } catch (error) {
      setManualContractorError(error instanceof Error ? error.message : 'Не удалось обновить данные контрагента');
    } finally {
      setIsUpdatingManualContractor(false);
    }
  };

  const manualContractorFieldErrors = manualContractorValidation.fieldErrors;
  const usersRoleFilterOptions = useMemo(
    () => Array.from(new Set(rows.map((row) => row.role))).map((role) => ({ label: role, value: role })),
    [rows]
  );
  const usersStatusFilterOptions = useMemo(
    () => inlineStatusOptions.map((status) => ({ label: userStatusLabelByValue[status], value: userStatusLabelByValue[status] })),
    []
  );
  const usersColumns = useMemo<TableTemplateColumn<UserRow>[]>(
    () => [
      { id: 'id', header: 'ID', field: 'id', minWidth: 150, width: '170px' },
      {
        id: 'full_name',
        header: 'ФИО',
        field: 'full_name',
        minWidth: 190,
        renderValue: (value) => <Typography variant="body2">{String(value ?? '—')}</Typography>
      },
      {
        id: 'phone',
        header: 'Телефон',
        field: 'phone',
        minWidth: 150,
        renderValue: (value) => <Typography variant="body2">{String(value ?? '—')}</Typography>
      },
      {
        id: 'mail',
        header: 'E-mail',
        field: 'mail',
        minWidth: 190,
        renderValue: (value) => <Typography variant="body2">{String(value ?? '—')}</Typography>
      },
      ...(canViewRoleIds ? [{ id: 'id_role', header: 'ID роли', field: 'id_role', minWidth: 100, width: '110px' } as TableTemplateColumn<UserRow>] : []),
      {
        id: 'role',
        header: 'Роль',
        minWidth: 180,
        filterKind: 'select',
        filterOptions: usersRoleFilterOptions,
        getFilterValue: (row) => row.role,
        getSearchValue: (row) => row.role,
        renderCell: (row) => {
          const canEditRoleForRow = Boolean(
            canUpdateRole
            && users.find((item) => item.user_id === row.id)?.actions.update_role
            && allowedRoleOptions.includes(row.id_role)
          );

          if (!canEditRoleForRow) {
            return <Typography variant="body2">{row.role}</Typography>;
          }

          return (
            <TextField
              select
              size="small"
              value={row.id_role}
              disabled={updatingUserId === row.id}
              onClick={(event) => event.stopPropagation()}
              onChange={(event) => {
                event.stopPropagation();
                const nextRoleId = Number(event.target.value);
                if (nextRoleId === row.id_role) {
                  return;
                }
                void handleInlineRoleChange(row.id, nextRoleId);
              }}
              sx={{ minWidth: 140 }}
            >
              {allowedRoleOptions.map((roleId) => (
                <MenuItem key={roleId} value={roleId}>
                  {getRoleLabel(roleId)}
                </MenuItem>
              ))}
            </TextField>
          );
        }
      },
      {
        id: 'status',
        header: 'Статус профиля',
        minWidth: 180,
        filterKind: 'select',
        filterOptions: usersStatusFilterOptions,
        getFilterValue: (row) => userStatusLabelByValue[row.status],
        getSearchValue: (row) => userStatusLabelByValue[row.status],
        renderCell: (row) => (
          <TextField
            select
            size="small"
            value={row.status}
            disabled={!canEditUserStatus(row.id) || updatingUserId === row.id}
            onClick={(event) => event.stopPropagation()}
            onChange={(event) => {
              event.stopPropagation();
              const nextStatus = event.target.value as StatusFormValues['user_status'];
              if (nextStatus === row.status) {
                return;
              }
              void handleInlineStatusChange(row.id, nextStatus);
            }}
            sx={{ minWidth: 140 }}
          >
            {inlineStatusOptions.map((status) => (
              <MenuItem key={status} value={status}>
                {userStatusLabelByValue[status]}
              </MenuItem>
            ))}
          </TextField>
        )
      }
    ],
    [allowedRoleOptions, canUpdateRole, canViewRoleIds, getRoleLabel, handleInlineRoleChange, handleInlineStatusChange, canEditUserStatus, updatingUserId, users, usersRoleFilterOptions, usersStatusFilterOptions]
  );
  const contractorStatusFilterOptions = useMemo(
    () => Array.from(new Set(users.map((user) => toStatusLabel(user.status)))).map((status) => ({ label: status, value: status })),
    [users]
  );
  const contractorColumnsTemplate = useMemo<TableTemplateColumn<UserListItem>[]>(
    () => [
      { id: 'login', header: 'Логин', field: 'user_id', minWidth: 170 },
      { id: 'full_name', header: 'ФИО', field: 'full_name', minWidth: 190, renderValue: (value) => <Typography variant="body2">{String(value ?? '—')}</Typography> },
      { id: 'phone', header: 'Телефон', field: 'phone', minWidth: 150, renderValue: (value) => <Typography variant="body2">{formatPhoneForView(value as string | null | undefined) ?? '—'}</Typography> },
      { id: 'mail', header: 'E-mail', field: 'mail', minWidth: 190, renderValue: (value) => <Typography variant="body2">{String(value ?? '—')}</Typography> },
      { id: 'company_phone', header: 'Телефон компании', field: 'company_phone', minWidth: 170, renderValue: (value) => <Typography variant="body2">{formatPhoneForView(value as string | null | undefined) ?? '—'}</Typography> },
      { id: 'company_mail', header: 'E-mail компании', field: 'company_mail', minWidth: 190, renderValue: (value) => <Typography variant="body2">{String(value ?? '—')}</Typography> },
      {
        id: 'status',
        header: 'Статус',
        field: 'status',
        minWidth: 150,
        filterKind: 'select',
        filterOptions: contractorStatusFilterOptions,
        getFilterValue: (row) => toStatusLabel(row.status),
        getSearchValue: (row) => toStatusLabel(row.status),
        renderCell: (row) => <ContractorStatusPill value={row.status} />
      }
    ],
    [contractorStatusFilterOptions]
  );

  if (!isContractorsTab) {
    return (
      <>
        <Stack spacing={1.2}>
          {inlineStatusError ? <Alert severity="error">{inlineStatusError}</Alert> : null}
          {inlineRoleError ? <Alert severity="error">{inlineRoleError}</Alert> : null}
          <TableTemplate
            columns={usersColumns}
            rows={rows}
            getRowId={(row) => row.id}
            isLoading={isLoading}
            noRowsLabel={emptyMessage}
            searchPlaceholder="Найти пользователя"
            addButtonLabel="Добавить пользователя"
            onAddClick={onAddClick}
            minTableWidth={840}
            cardExpansionControl={{
              checked: rows.length > 0 && rows.every((row) => Boolean(expandedUserCardsById[row.id])),
              onChange: (checked) => {
                setExpandedUserCardsById(
                  Object.fromEntries(rows.map((row) => [row.id, checked]))
                );
              },
              openLabel: 'Развернуть все',
              closeLabel: 'Свернуть все'
            }}
            getCardPrimaryText={(row) => row.id}
            getCardSecondaryText={(row) => row.full_name}
            cardExcludedColumnIds={['id']}
            renderCard={(row) => (
              <UserMobileCard
                row={row}
                canViewRoleIds={canViewRoleIds}
                isExpanded={Boolean(expandedUserCardsById[row.id])}
                onToggleExpand={() =>
                  setExpandedUserCardsById((prev) => ({
                    ...prev,
                    [row.id]: !prev[row.id]
                  }))
                }
                onOpenDetails={(clickedRow) => {
                  const clickedUser = users.find((item) => item.user_id === clickedRow.id);
                  if (clickedUser) {
                    setSelectedUser(clickedUser);
                    setSubordinateProfile(null);
                    setSubordinateError(null);
                    setManagerOptions([]);
                    setManagerError(null);
                    setManagerUserId(clickedUser.id_parent ?? '');
                    setOpenSubordinateUnavailability(false);
                    void getSubordinateProfile(clickedUser.user_id)
                      .then((profile) => setSubordinateProfile(profile))
                      .catch((error) => {
                        setSubordinateError(error instanceof Error ? error.message : 'Не удалось загрузить нерабочие статусы');
                      });
                  }
                }}
              />
            )}
            onRowClick={(row) => {
              const clickedUser = users.find((item) => item.user_id === row.id);
              if (clickedUser) {
                setSelectedUser(clickedUser);
                setSubordinateProfile(null);
                setSubordinateError(null);
                setManagerOptions([]);
                setManagerError(null);
                setManagerUserId(clickedUser.id_parent ?? '');
                setOpenSubordinateUnavailability(false);
                void getSubordinateProfile(clickedUser.user_id)
                  .then((profile) => setSubordinateProfile(profile))
                  .catch((error) => {
                    setSubordinateError(error instanceof Error ? error.message : 'Не удалось загрузить нерабочие статусы');
                  });
              }
            }}
          />
        </Stack>

        <Dialog
          open={Boolean(selectedUser)}
          onClose={() => {
            setSelectedUser(null);
            setOpenSubordinateUnavailability(false);
          }}
          maxWidth="sm"
          fullWidth
          aria-labelledby="user-card-dialog-title"
          PaperProps={{
            sx: dialogPaperSx
          }}
        >
          <DialogContent sx={dialogContentSx}>
            {selectedUser ? (
              <Stack spacing={2}>
                <Typography id="user-card-dialog-title" variant="h5" fontWeight={600} lineHeight={1}>
                  Карточка пользователя
                </Typography>

                <Box
                  sx={{
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    p: { xs: 1.4, sm: 1.6 },
                    backgroundColor: 'background.paper'
                  }}
                >
                  <Stack spacing={1.2}>
                    <SourceSection title="Пользователь" source="users">
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                          gap: 1.5
                        }}
                      >
                        <InfoRow label="Логин" value={selectedUser.user_id} />
                        <Stack spacing={0.2} sx={{ alignItems: 'flex-start' }}>
                          <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                            Статус users
                          </Typography>
                          <UserStatusPill value={selectedUser.status} />
                        </Stack>
                      </Box>
                    </SourceSection>

                    <SourceSection title="Профиль пользователя" source="profiles">
                      <Stack spacing={1.2}>
                        <InfoRow label="ФИО" value={selectedUser.full_name} />
                        <Box
                          sx={{
                            display: 'grid',
                            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                            gap: 1.2
                          }}
                        >
                          <InfoRow label="Телефон" value={formatPhoneForView(selectedUser.phone)} />
                          <InfoRow label="E-mail" value={selectedUser.mail} />
                        </Box>
                      </Stack>
                    </SourceSection>
                  </Stack>
                </Box>

                {subordinateProfile ? (
                  <Stack spacing={1.2}>
                    {subordinateError ? <Alert severity="warning">{subordinateError}</Alert> : null}
                    <UnavailabilityManagementSection
                      currentPeriod={subordinateProfile.unavailablePeriod}
                      periods={subordinateProfile.unavailablePeriods}
                      canEdit={subordinateProfile.actions.manage_subordinate_unavailability}
                      isDialogOpen={openSubordinateUnavailability}
                      onOpenDialog={() => setOpenSubordinateUnavailability(true)}
                      onCloseDialog={() => setOpenSubordinateUnavailability(false)}
                      onSubmit={handleSubordinateUnavailabilitySubmit(async (values) => {
                        if (!selectedUser) {
                          return;
                        }

                        const newPeriodStart = new Date(values.started_at).toISOString();
                        const newPeriodEnd = new Date(values.ended_at).toISOString();

                        const overlapPeriod = subordinateProfile.unavailablePeriods.find((period) =>
                          hasPeriodOverlapByDate(newPeriodStart, newPeriodEnd, period.startedAt, period.endedAt)
                        );
                        if (overlapPeriod) {
                          const startedAt = new Date(overlapPeriod.startedAt).toLocaleDateString('ru-RU');
                          const endedAt = new Date(overlapPeriod.endedAt).toLocaleDateString('ru-RU');
                          setSubordinateError(`Период пересекается с уже существующим периодом (${startedAt} — ${endedAt})`);
                          return;
                        }

                        setSubordinateError(null);
                        const nextProfile = await setSubordinateUnavailabilityPeriod(selectedUser.user_id, {
                          status: values.status,
                          started_at: newPeriodStart,
                          ended_at: newPeriodEnd
                        });
                        setSubordinateProfile(nextProfile);
                        setOpenSubordinateUnavailability(false);
                      })}
                      isSubmitting={isSubmittingSubordinateUnavailability}
                      dialogTitle="Установить нерабочий период"
                      triggerLabel="Установить нерабочий период"
                      submitLabel="Сохранить период"
                      dialogNotice={subordinateError ? <Alert severity="warning">{subordinateError}</Alert> : null}
                      editor={
                        <UnavailabilityPeriodEditor
                          statusField={registerSubordinateUnavailability('status')}
                          startedAtField={registerSubordinateUnavailability('started_at')}
                          endedAtField={registerSubordinateUnavailability('ended_at')}
                          startedAtValue={watchSubordinateUnavailability('started_at') ?? ''}
                          endedAtValue={watchSubordinateUnavailability('ended_at') ?? ''}
                          onStartedAtChange={(value: string) =>
                            setSubordinateUnavailabilityValue('started_at', value, { shouldValidate: true, shouldDirty: true })
                          }
                          onEndedAtChange={(value: string) =>
                            setSubordinateUnavailabilityValue('ended_at', value, { shouldValidate: true, shouldDirty: true })
                          }
                          statusError={subordinateUnavailabilityErrors.status?.message}
                          startedAtError={subordinateUnavailabilityErrors.started_at?.message}
                          endedAtError={subordinateUnavailabilityErrors.ended_at?.message}
                        />
                      }
                    />
                  </Stack>
                ) : subordinateError ? (
                  <Alert severity="info">{subordinateError}</Alert>
                ) : null}

                {selectedUser.actions.update_manager ? (
                  <Stack
                    spacing={1.2}
                    sx={{
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1,
                      p: { xs: 1.4, sm: 1.8 },
                      backgroundColor: 'background.paper'
                    }}
                  >
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'text.primary' }}>
                      Смена руководителя
                    </Typography>
                    {managerError ? <Alert severity="warning">{managerError}</Alert> : null}
                    <TextField
                      select
                      size="small"
                      label="Новый руководитель"
                      value={managerUserId}
                      onChange={(event) => setManagerUserId(event.target.value)}
                      disabled={isUpdatingManager || managerOptions.filter((manager) => manager.user_id !== selectedUser.user_id).length === 0}
                      helperText={
                        managerOptions.filter((manager) => manager.user_id !== selectedUser.user_id).length
                          ? ''
                          : 'Нет доступных руководителей'
                      }
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          borderRadius: 1,
                          backgroundColor: 'background.paper'
                        }
                      }}
                    >
                      {managerOptions
                        .filter((manager) => manager.user_id !== selectedUser.user_id)
                        .map((manager) => (
                          <MenuItem key={manager.user_id} value={manager.user_id}>
                            {manager.full_name ? `${manager.full_name} (${manager.user_id})` : manager.user_id}
                          </MenuItem>
                        ))}
                    </TextField>
                    <Stack direction="row" justifyContent="flex-end">
                      <Button
                        variant="outlined"
                        onClick={() => void handleManagerUpdate()}
                        disabled={
                          !managerUserId
                          || managerUserId === selectedUser.id_parent
                          || isUpdatingManager
                          || managerOptions.filter((manager) => manager.user_id !== selectedUser.user_id).length === 0
                        }
                        sx={{ borderRadius: 1, textTransform: 'none' }}
                      >
                        {isUpdatingManager ? 'Сохранение...' : 'Сохранить руководителя'}
                      </Button>
                    </Stack>
                  </Stack>
                ) : null}


                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.2} justifyContent="flex-end">
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setSelectedUser(null);
                      setOpenSubordinateUnavailability(false);
                    }}
                    sx={{ borderRadius: 1, textTransform: 'none' }}
                  >
                    Закрыть
                  </Button>
                </Stack>
              </Stack>
            ) : null}
          </DialogContent>
        </Dialog>
      </>
    );
  }

  return (
    <>
      <TableTemplate
        columns={contractorColumnsTemplate}
        rows={users}
        getRowId={(row) => row.user_id}
        isLoading={isLoading}
        noRowsLabel={emptyMessage}
        searchPlaceholder="Найти контрагента"
        addButtonLabel="Добавить контрагента"
        onAddClick={onAddClick}
        minTableWidth={980}
        cardExpansionControl={{
          checked: users.length > 0
            && users.every((row) =>
              Boolean(expandedContractorCardsById[row.user_id]?.contact)
              && Boolean(expandedContractorCardsById[row.user_id]?.company)
            ),
          onChange: (checked) => {
            setExpandedContractorCardsById(
              Object.fromEntries(
                users.map((row) => [
                  row.user_id,
                  {
                    contact: checked,
                    company: checked
                  }
                ])
              )
            );
          },
          openLabel: 'Развернуть все',
          closeLabel: 'Свернуть все'
        }}
        getCardPrimaryText={(row) => row.company_name ?? row.full_name ?? row.user_id}
        getCardSecondaryText={(row) => row.user_id}
        cardExcludedColumnIds={['login']}
        renderCard={(row) => (
          <ContractorMobileCard
            row={row}
            isContactExpanded={Boolean(expandedContractorCardsById[row.user_id]?.contact)}
            isCompanyExpanded={Boolean(expandedContractorCardsById[row.user_id]?.company)}
            onToggleContact={() =>
              setExpandedContractorCardsById((prev) => ({
                ...prev,
                [row.user_id]: {
                  contact: !prev[row.user_id]?.contact,
                  company: Boolean(prev[row.user_id]?.company)
                }
              }))
            }
            onToggleCompany={() =>
              setExpandedContractorCardsById((prev) => ({
                ...prev,
                [row.user_id]: {
                  contact: Boolean(prev[row.user_id]?.contact),
                  company: !prev[row.user_id]?.company
                }
              }))
            }
            onOpenDetails={(clickedRow) => {
              setSelectedUser(clickedRow);
              setSubmitError(null);
              setSubmitSuccess(null);
            }}
          />
        )}
        onRowClick={(row) => {
          setSelectedUser(row);
          setSubmitError(null);
          setSubmitSuccess(null);
        }}
      />

      <Dialog
        open={Boolean(selectedUser)}
        onClose={() => setSelectedUser(null)}
        maxWidth="md"
        fullWidth
        aria-labelledby="contractor-card-dialog-title"
        PaperProps={{
          sx: dialogPaperSx
        }}
      >
        <DialogContent sx={dialogContentSx}>
          {selectedUser ? (
            <Stack spacing={2}>
              <Typography id="contractor-card-dialog-title" variant="h5" fontWeight={600} lineHeight={1}>
                Карточка контрагента
              </Typography>

              <Box
                sx={{
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  p: { xs: 1.4, sm: 1.6 },
                  backgroundColor: 'background.paper'
                }}
              >
                <Stack spacing={1.2}>
                  <SourceSection title="Пользователь" source="users">
                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                        gap: 1.5
                      }}
                    >
                      <InfoRow label="Логин" value={selectedUser.user_id} />
                      <Stack spacing={0.2} sx={{ alignItems: 'flex-start' }}>
                        <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          Статус users
                        </Typography>
                        <UserStatusPill value={selectedUser.status} />
                      </Stack>
                    </Box>
                  </SourceSection>

                  <SourceSection title="Профиль пользователя" source="profiles">
                    <Stack spacing={1.2}>
                      <InfoRow label="ФИО" value={selectedUser.full_name} />
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                          gap: 1.2
                        }}
                      >
                        <InfoRow label="Телефон" value={formatPhoneForView(selectedUser.phone)} />
                        <InfoRow label="E-mail" value={selectedUser.mail} />
                      </Box>
                    </Stack>
                  </SourceSection>

                  <SourceSection title="Контакты компании" source="company_contacts">
                    <Stack spacing={1.2}>
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                          gap: 1.2
                        }}
                      >
                        <InfoRow label="ИНН" value={selectedUser.inn} />
                        <InfoRow label="Компания" value={selectedUser.company_name} />
                      </Box>

                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                          gap: 1.2
                        }}
                      >
                        <InfoRow label="Телефон компании" value={formatPhoneForView(selectedUser.company_phone)} />
                        <InfoRow label="E-mail компании" value={selectedUser.company_mail} />
                        <InfoRow label="Адрес" value={selectedUser.address} />
                      </Box>
                      <InfoRow label="Примечание" value={selectedUser.note} />
                    </Stack>
                  </SourceSection>

                </Stack>
              </Box>

              {selectedUser.actions.manage_manual_contractor ? (
                <Stack
                  spacing={1.2}
                  sx={{
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    p: { xs: 1.4, sm: 1.8 },
                    backgroundColor: 'background.paper'
                  }}
                >
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'text.primary' }}>
                    Редактирование данных
                  </Typography>
                  <Box
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                      gap: 1.2
                    }}
                  >
                    <TextField
                      label="Логин"
                      value={manualContractorDraft.login}
                      onChange={(event) => updateManualContractorField('login', event.target.value)}
                      error={Boolean(manualContractorFieldErrors.login)}
                      helperText={manualContractorFieldErrors.login}
                    />
                    <TextField
                      label="Новый пароль"
                      type="password"
                      placeholder="Оставьте пустым, если без смены"
                      value={manualContractorPassword}
                      onChange={(event) => handleManualContractorPasswordChange(event.target.value)}
                      error={Boolean(manualContractorFieldErrors.password)}
                      helperText={manualContractorFieldErrors.password}
                    />
                    <TextField
                      label="ФИО"
                      value={manualContractorDraft.full_name}
                      onChange={(event) => updateManualContractorField('full_name', event.target.value)}
                      error={Boolean(manualContractorFieldErrors.full_name)}
                      helperText={manualContractorFieldErrors.full_name}
                    />
                    <TextField
                      label="Телефон"
                      value={manualContractorDraft.phone}
                      onChange={(event) => updateManualContractorField('phone', formatRuPhone(event.target.value))}
                      placeholder="+7 (900) 999-88-77"
                      error={Boolean(manualContractorFieldErrors.phone)}
                      helperText={manualContractorFieldErrors.phone}
                    />
                    <TextField
                      label="E-mail"
                      value={manualContractorDraft.mail}
                      onChange={(event) => updateManualContractorField('mail', event.target.value)}
                      error={Boolean(manualContractorFieldErrors.mail)}
                      helperText={manualContractorFieldErrors.mail}
                    />
                    <TextField
                      label="Компания"
                      value={manualContractorDraft.company_name}
                      onChange={(event) => updateManualContractorField('company_name', event.target.value)}
                      error={Boolean(manualContractorFieldErrors.company_name)}
                      helperText={manualContractorFieldErrors.company_name}
                    />
                    <TextField
                      label="ИНН"
                      value={manualContractorDraft.inn}
                      onChange={(event) => updateManualContractorField('inn', event.target.value)}
                      error={Boolean(manualContractorFieldErrors.inn)}
                      helperText={manualContractorFieldErrors.inn}
                    />
                    <TextField
                      label="Телефон компании"
                      value={manualContractorDraft.company_phone}
                      onChange={(event) => updateManualContractorField('company_phone', formatRuPhone(event.target.value))}
                      placeholder="+7 (900) 999-88-77"
                      error={Boolean(manualContractorFieldErrors.company_phone)}
                      helperText={manualContractorFieldErrors.company_phone}
                    />
                    <TextField
                      label="E-mail компании"
                      value={manualContractorDraft.company_mail}
                      onChange={(event) => updateManualContractorField('company_mail', event.target.value)}
                      error={Boolean(manualContractorFieldErrors.company_mail)}
                      helperText={manualContractorFieldErrors.company_mail}
                    />
                    <TextField
                      label="Адрес"
                      value={manualContractorDraft.address}
                      onChange={(event) => updateManualContractorField('address', event.target.value)}
                      error={Boolean(manualContractorFieldErrors.address)}
                      helperText={manualContractorFieldErrors.address}
                    />
                  </Box>
                  <TextField
                    label="Примечание"
                    value={manualContractorDraft.note}
                    onChange={(event) => updateManualContractorField('note', event.target.value)}
                    multiline
                    minRows={2}
                    error={Boolean(manualContractorFieldErrors.note)}
                    helperText={manualContractorFieldErrors.note}
                  />
                  {manualContractorError ? <Alert severity="error">{manualContractorError}</Alert> : null}
                  {manualContractorSuccess ? <Alert severity="success">{manualContractorSuccess}</Alert> : null}
                  <Stack direction="row" justifyContent="flex-end">
                    <Button
                      variant="outlined"
                      onClick={() => void handleManualContractorSave()}
                      disabled={
                        isUpdatingManualContractor
                        || !manualContractorValidation.hasChanges
                        || Boolean(manualContractorValidation.firstError)
                      }
                      sx={{ borderRadius: 1, textTransform: 'none' }}
                    >
                      {isUpdatingManualContractor ? 'Сохранение...' : 'Сохранить данные'}
                    </Button>
                  </Stack>
                </Stack>
              ) : null}

              {canUpdateStatus ? (
                <Stack
                  spacing={1.2}
                  sx={{
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    p: { xs: 1.4, sm: 1.8 },
                    backgroundColor: 'background.paper'
                  }}
                >
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'text.primary' }}>
                    Изменение статуса
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <TextField
                      label="Изменить статус"
                      select
                      fullWidth
                      defaultValue={normalizeUserStatus(selectedUser.status)}
                      {...register('user_status')}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          borderRadius: 1,
                          backgroundColor: 'background.paper'
                        }
                      }}
                    >
                      <MenuItem value="review">На проверке</MenuItem>
                      <MenuItem value="active">Активен</MenuItem>
                      <MenuItem value="inactive">Неактивен</MenuItem>
                      <MenuItem value="blacklist">В черном списке</MenuItem>
                    </TextField>
                    <Tooltip
                      arrow
                      placement="top-start"
                      title={
                        <Typography
                          variant="body2"
                          sx={{
                            m: 0,
                            whiteSpace: 'pre-line',
                            lineHeight: 1.45
                          }}
                        >
                          {statusMemoText}
                        </Typography>
                      }
                      slotProps={{
                        tooltip: {
                          sx: {
                            maxWidth: 380,
                            p: 1.4,
                            borderRadius: 2
                          }
                        }
                      }}
                    >
                      <Box
                        component="span"
                        sx={{
                          width: 24,
                          height: 24,
                          borderRadius: '50%',
                          border: '1px solid',
                          borderColor: 'primary.main',
                          color: 'primary.main',
                          fontSize: 14,
                          fontWeight: 700,
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          cursor: 'pointer'
                        }}
                      >
                        ?
                      </Box>
                    </Tooltip>
                  </Stack>

                  {submitError ? <Alert severity="error">{submitError}</Alert> : null}
                  {submitSuccess ? <Alert severity="success">{submitSuccess}</Alert> : null}

                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.2} justifyContent="flex-end">
                    <Button variant="outlined" onClick={() => setSelectedUser(null)} sx={{ borderRadius: 1, textTransform: 'none' }}>
                      Закрыть
                    </Button>
                    <Button
                      variant="contained"
                      onClick={handleSubmit(handleStatusSubmit)}
                      disabled={isSubmitting}
                      sx={{ borderRadius: 1, textTransform: 'none', minWidth: 180, boxShadow: 'none' }}
                    >
                      {isSubmitting ? 'Сохранение...' : 'Сохранить статус'}
                    </Button>
                  </Stack>
                </Stack>
              ) : (
                <Alert severity="info">Изменение статуса недоступно: backend не вернул доступное действие.</Alert>
              )}
            </Stack>
          ) : null}
        </DialogContent>
      </Dialog>
    </>
  );
};


