import ExpandMoreRounded from '@mui/icons-material/ExpandMoreRounded';
import {
  ButtonBase,
  Collapse,
  Divider,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import type { MouseEvent as ReactMouseEvent, ReactNode } from 'react';
import type { UserListItem } from '@entities/user';
import { EmailWithVerifiedMark } from '@features/admin/components/UserCardPrimitives';
import { ContractorStatusPill, formatPhoneForView } from './contractorUi';

type ContractorMobileCardProps = {
  row: UserListItem;
  canViewEmailVerification?: boolean;
  isContactExpanded: boolean;
  isCompanyExpanded: boolean;
  onToggleContact: () => void;
  onToggleCompany: () => void;
  onOpenDetails?: (row: UserListItem) => void;
};

export const ContractorMobileCard = ({
  row,
  canViewEmailVerification = false,
  isContactExpanded,
  isCompanyExpanded,
  onToggleContact,
  onToggleCompany,
  onOpenDetails,
}: ContractorMobileCardProps) => {
  const theme = useTheme();
  const name = row.full_name?.trim();
  const title = name ? `${name} (${row.user_id})` : row.user_id;
  const contactRows: Array<{ key: string; label: string; value: ReactNode }> = [
    { key: 'phone', label: 'Телефон', value: formatPhoneForView(row.phone) ?? '—' },
    {
      key: 'mail',
      label: 'Почта',
      value: (
        <EmailWithVerifiedMark
          mail={row.mail}
          verified={Boolean(row.email_verified)}
          showMark={canViewEmailVerification}
        />
      ),
    },
  ];
  const companyRows = [
    { key: 'company_phone', label: 'Телефон', value: formatPhoneForView(row.company_phone) ?? '—' },
    { key: 'company_mail', label: 'Почта', value: row.company_mail ?? '—' },
    { key: 'company_name', label: 'Компания', value: row.company_name ?? '—' },
    { key: 'inn', label: 'ИНН', value: row.inn ?? '—' },
    { key: 'address', label: 'Адрес', value: row.address ?? '—' },
    { key: 'note', label: 'Примечание', value: row.note ?? '—' },
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
          boxShadow: `0 6px 14px ${alpha(theme.palette.common.black, 0.08)}`,
        },
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
              color: 'text.primary',
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
                bgcolor: alpha(theme.palette.primary.main, 0.06),
              },
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
                  color: 'primary.main',
                }}
              >
                Для связи
              </Typography>
              <ExpandMoreRounded
                sx={{
                  fontSize: 20,
                  color: 'primary.main',
                  transform: isContactExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.28s ease',
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
                        fontSize: 12,
                        fontWeight: 600,
                        color: 'text.secondary',
                        textTransform: 'uppercase',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {detail.label}
                    </Typography>
                    <Typography
                      sx={{
                        minWidth: 0,
                        flex: 1,
                        fontSize: 14,
                        lineHeight: 1.3,
                        fontWeight: 500,
                        color: detail.value === '—' ? 'text.secondary' : 'text.primary',
                        whiteSpace: 'normal',
                        wordBreak: 'break-word',
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
                bgcolor: alpha(theme.palette.primary.main, 0.06),
              },
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
                  color: 'primary.main',
                }}
              >
                Компания
              </Typography>
              <ExpandMoreRounded
                sx={{
                  fontSize: 20,
                  color: 'primary.main',
                  transform: isCompanyExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.28s ease',
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
                        fontSize: 12,
                        fontWeight: 600,
                        color: 'text.secondary',
                        textTransform: 'uppercase',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {detail.label}
                    </Typography>
                    <Typography
                      sx={{
                        minWidth: 0,
                        flex: 1,
                        fontSize: 14,
                        lineHeight: 1.3,
                        fontWeight: 500,
                        color: detail.value === '—' ? 'text.secondary' : 'text.primary',
                        whiteSpace: 'normal',
                        wordBreak: 'break-word',
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
