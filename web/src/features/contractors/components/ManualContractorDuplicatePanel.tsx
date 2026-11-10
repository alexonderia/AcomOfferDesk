import { useState } from 'react';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import { Alert, Box, Button, ButtonBase, Card, CardContent, Chip, Divider, Stack, Tooltip, Typography } from '@mui/material';
import type { ManualContractorDuplicate } from '@shared/api/users/getManualContractorDuplicates';
import { formatDate } from '@shared/lib/formatters';
import { useManualContractorDuplicates } from '../model/useManualContractorDuplicates';

type ManualContractorDuplicatePanelProps = {
  open: boolean;
  companyName?: string;
  inn?: string;
  companyMail?: string;
  requestId?: string;
  onSelect?: (item: ManualContractorDuplicate) => void;
  disabled?: boolean;
};

export const ManualContractorDuplicatePanel = ({
  open,
  companyName = '',
  inn = '',
  companyMail = '',
  requestId,
  onSelect,
  disabled = false,
}: ManualContractorDuplicatePanelProps) => {
  const { duplicates, loading, error, hasQuery, reload } = useManualContractorDuplicates({
    open, companyName, inn, companyMail, requestId,
  });

  if (!open || (!hasQuery && !loading && duplicates.length === 0)) return null;

  return (
    <Box
      component="aside"
      sx={{
        width: requestId ? '100%' : { xs: '100%', md: 320 },
        minWidth: 0,
        flexShrink: 0,
        border: '1px solid',
        borderColor: duplicates.length ? 'warning.main' : 'divider',
        borderRadius: 2,
        p: 2,
        bgcolor: 'background.paper',
      }}
    >
      <Box sx={{ fontWeight: 700, mb: 1 }}>Возможные дубликаты</Box>
      {loading ? <Box sx={{ color: 'text.secondary', fontSize: 14 }}>Проверяем введённые данные…</Box> : null}
      {error ? <Alert severity="error" action={<Button onClick={reload}>Повторить</Button>}>{error}</Alert> : null}
      {!loading && !error && duplicates.length === 0 ? (
        <Box sx={{ color: 'text.secondary', fontSize: 14 }}>Совпадений не найдено.</Box>
      ) : null}
      <Stack spacing={1.5}>
        {duplicates.map((item) => <DuplicateCard
          key={item.userId} item={item} compact={Boolean(requestId)}
          onSelect={onSelect} disabled={disabled || (Boolean(requestId) && item.canSelect !== true)}
        />)}
      </Stack>
    </Box>
  );
};

const InfoRow = ({ label, value }: { label: string; value: string }) => (
  <Box sx={{ display: 'grid', gridTemplateColumns: 'minmax(90px, 1fr) minmax(0, 1.5fr)', gap: 1, py: 0.65 }}>
    <Typography sx={{ color: 'text.secondary', fontSize: 12, fontWeight: 500 }}>{label}</Typography>
    <Typography sx={{ fontSize: 13, overflowWrap: 'anywhere' }}>{value}</Typography>
  </Box>
);

const DuplicateCard = ({ item, onSelect, disabled, compact }: {
  item: ManualContractorDuplicate;
  onSelect?: (item: ManualContractorDuplicate) => void;
  disabled: boolean;
  compact: boolean;
}) => {
  const [contactExpanded, setContactExpanded] = useState(!compact);
  const [companyExpanded, setCompanyExpanded] = useState(!compact);
  const valueOrPlaceholder = (value: string | null) => value?.trim() || 'Не указано';
  const statusLabel = (status: string) => ({
    active: 'Активен',
    review: 'На проверке',
    blocked: 'Заблокирован',
    inactive: 'Неактивен',
    blacklist: 'В чёрном списке',
  }[status] ?? status);

  return (
    <Card variant="outlined" sx={{ borderRadius: 2, boxShadow: 'none' }}>
      <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
          <Typography noWrap sx={{ minWidth: 0, fontWeight: 700 }} title={valueOrPlaceholder(item.companyName)}>
            {valueOrPlaceholder(item.companyName)}
          </Typography>
          <Chip
            size="small"
            label={statusLabel(item.status)}
            color={item.status === 'active' ? 'success' : 'default'}
            variant="outlined"
            sx={{ flexShrink: 0, maxWidth: 125 }}
          />
        </Stack>
        {compact && item.inn ? <Typography variant="body2" sx={{ mt: 1 }}>ИНН: {item.inn}</Typography> : null}
        {onSelect ? (
          <Tooltip title={item.disabledReason ?? ''} describeChild disableInteractive>
            <span>
              <Button fullWidth disabled={disabled} onClick={() => onSelect(item)}>
                Использовать этого контрагента
              </Button>
            </span>
          </Tooltip>
        ) : null}
        {item.disabledReason ? <Typography variant="caption" color="text.secondary">{item.disabledReason}</Typography> : null}
        <Divider sx={{ my: 1 }} />
        <SectionToggle label="ДЛЯ СВЯЗИ" expanded={contactExpanded} onClick={() => setContactExpanded((value) => !value)} />
        {contactExpanded ? (
          <Stack divider={<Divider flexItem />}>
            <InfoRow label="ФИО" value={valueOrPlaceholder(item.fullName)} />
            <InfoRow label="ТЕЛЕФОН" value={valueOrPlaceholder(item.phone)} />
            <InfoRow label="ПОЧТА" value={valueOrPlaceholder(item.mail)} />
          </Stack>
        ) : null}
        <SectionToggle label="КОМПАНИЯ" expanded={companyExpanded} onClick={() => setCompanyExpanded((value) => !value)} />
        {companyExpanded ? (
          <Stack divider={<Divider flexItem />}>
            <InfoRow label="ТЕЛЕФОН" value={valueOrPlaceholder(item.companyPhone)} />
            <InfoRow label="ПОЧТА" value={valueOrPlaceholder(item.companyMail)} />
            <InfoRow label="КОМПАНИЯ" value={valueOrPlaceholder(item.companyName)} />
            <InfoRow label="ИНН" value={valueOrPlaceholder(item.inn)} />
            <InfoRow label="АДРЕС" value={valueOrPlaceholder(item.address)} />
            <InfoRow label="ПРИМЕЧАНИЕ" value={valueOrPlaceholder(item.note)} />
          </Stack>
        ) : null}
        {item.createdAt || item.updatedAt ? (
          <Stack sx={{ mt: 1 }}>
            {item.createdAt ? <InfoRow label="СОЗДАН" value={formatDate(item.createdAt, true)} /> : null}
            {item.updatedAt ? <InfoRow label="ИЗМЕНЁН" value={formatDate(item.updatedAt, true)} /> : null}
          </Stack>
        ) : null}
      </CardContent>
    </Card>
  );
};

const SectionToggle = ({ label, expanded, onClick }: { label: string; expanded: boolean; onClick: () => void }) => (
  <ButtonBase
    onClick={onClick}
    sx={{ width: '100%', justifyContent: 'space-between', color: 'primary.main', py: 0.5, mt: 0.5 }}
  >
    <Typography sx={{ fontWeight: 700, fontSize: 13 }}>{label}</Typography>
    {expanded ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
  </ButtonBase>
);
