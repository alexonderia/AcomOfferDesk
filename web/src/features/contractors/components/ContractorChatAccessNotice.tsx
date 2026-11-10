import { IconButton, Tooltip } from '@mui/material';
import WarningAmberRoundedIcon from '@mui/icons-material/WarningAmberRounded';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import type { ContractorLoginAccess } from '@shared/api/contractors/getContractorLoginAccess';

type Props = { access?: ContractorLoginAccess; loading?: boolean };

export const ContractorChatAccessNotice = ({ access, loading }: Props) => {
  if (loading || !access || access.state === 'available' || access.state === 'setup_required') return null;
  const unknown = access.state === 'unknown';
  const description = unknown
      ? 'Не удалось проверить доступ контрагента к системе. Возможность прочитать сообщения в личном кабинете не подтверждена.'
      : `Контрагент не может войти в систему: ${access.label.toLocaleLowerCase('ru-RU')}. Он не сможет прочитать новые сообщения в личном кабинете, пока вход недоступен.`;
  return <Tooltip title={description} describeChild arrow placement="top" enterDelay={0} enterNextDelay={0} enterTouchDelay={250}>
    <IconButton type="button" color={unknown ? 'info' : 'warning'}
      aria-label={unknown ? 'Не удалось проверить доступ контрагента' : 'У контрагента нет доступа к системе'}
      sx={{ cursor: 'help', flexShrink: 0, color: unknown ? 'info.main' : 'warning.main' }}>
      {unknown ? <InfoOutlinedIcon fontSize="small" /> : <WarningAmberRoundedIcon fontSize="small" />}
    </IconButton>
  </Tooltip>;
};
