import { Box, CircularProgress, Tooltip } from '@mui/material';
import CheckCircleOutlineRoundedIcon from '@mui/icons-material/CheckCircleOutlineRounded';
import NoAccountsOutlinedIcon from '@mui/icons-material/NoAccountsOutlined';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import HourglassEmptyRoundedIcon from '@mui/icons-material/HourglassEmptyRounded';
import KeyOffOutlinedIcon from '@mui/icons-material/KeyOffOutlined';
import ManageAccountsOutlinedIcon from '@mui/icons-material/ManageAccountsOutlined';
import LockClockOutlinedIcon from '@mui/icons-material/LockClockOutlined';
import HelpOutlineRoundedIcon from '@mui/icons-material/HelpOutlineRounded';
import type { ContractorLoginAccess } from '@shared/api/contractors/getContractorLoginAccess';
import { StatusPill, type StatusPillTone } from '@shared/ui/StatusPill';

export const ContractorLoginAccessBadge = ({ access, loading = false, iconOnly = false }: { access?: ContractorLoginAccess; loading?: boolean; iconOnly?: boolean }) => {
  const label = loading ? 'Проверка…' : access?.label ?? 'Не удалось проверить';
  const description = loading ? 'Проверяем возможность входа в личный кабинет.'
    : access?.description ?? 'Не удалось подтвердить возможность входа. Повторите проверку в карточке контрагента.';
  const tones: Record<ContractorLoginAccess['state'], StatusPillTone> = {
    available: 'success', not_granted: 'neutral', blocked: 'error', pending: 'warning',
    password_not_set: 'warning', setup_required: 'warning', temporarily_locked: 'warning', unknown: 'neutral',
  };
  const icons = {
    available: CheckCircleOutlineRoundedIcon, not_granted: NoAccountsOutlinedIcon, blocked: LockOutlinedIcon,
    pending: HourglassEmptyRoundedIcon, password_not_set: KeyOffOutlinedIcon, setup_required: ManageAccountsOutlinedIcon,
    temporarily_locked: LockClockOutlinedIcon, unknown: HelpOutlineRoundedIcon,
  };
  const tone = loading ? 'info' : access ? tones[access.state] ?? 'neutral' : 'neutral';
  const AccessIcon = icons[access?.state ?? 'unknown'];
  return <Tooltip title={iconOnly ? `${label}. ${description}` : description} describeChild disableInteractive placement="top" arrow
    enterDelay={0} enterNextDelay={0} enterTouchDelay={250}>
    <Box component="span" tabIndex={0} aria-label={`Вход в личный кабинет: ${label}`}
      onClick={iconOnly ? (event) => event.stopPropagation() : undefined}
      sx={{ display: 'inline-flex', maxWidth: '100%', cursor: 'help',
        ...(iconOnly ? { width: 28, height: 28, flexShrink: 0, alignItems: 'center', justifyContent: 'center',
          color: tone === 'neutral' ? 'text.secondary' : `${tone}.main` } : {}) }}>
      {iconOnly
        ? loading ? <CircularProgress size={18} color="inherit" /> : <AccessIcon fontSize="small" />
        : <StatusPill label={label} tone={tone} />}
    </Box>
  </Tooltip>;
};
