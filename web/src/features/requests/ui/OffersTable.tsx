import { MouseEvent as ReactMouseEvent, useState, type ReactNode } from 'react';
import AccessTimeOutlinedIcon from '@mui/icons-material/AccessTimeOutlined';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ExpandMoreRounded from '@mui/icons-material/ExpandMoreRounded';
import HighlightOffOutlinedIcon from '@mui/icons-material/HighlightOffOutlined';
import MarkEmailUnreadRounded from '@mui/icons-material/MarkEmailUnreadRounded';
import RemoveOutlinedIcon from '@mui/icons-material/RemoveOutlined';
import ReportProblemOutlinedIcon from '@mui/icons-material/ReportProblemOutlined';
import { Box, ButtonBase, Chip, Collapse, Divider, MenuItem, Paper, Select, Stack, Tooltip, Typography } from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import type { RequestDetailsOffer } from '@shared/api/requests/getRequestDetails';
import { StatusPill } from '@shared/components/StatusPill';
import { TableTemplate, type TableTemplateColumn } from '@shared/components/TableTemplate';
import { formatDate, formatAmount } from '@shared/lib/formatters';

export type OfferDecisionStatus = 'accepted' | 'rejected' | '';

export type OfferStatusOption = {
  value: OfferDecisionStatus;
  label: string;
};

type OfferMobileCardProps = {
  offer: RequestDetailsOffer;
  selectedStatus: OfferDecisionStatus;
  statusOptions: OfferStatusOption[];
  acceptedOfferId?: number | null;
  canChangeStatus: boolean;
  onStatusChange: (offerId: number, value: OfferDecisionStatus) => void;
  onDownloadFile: (downloadUrl: string, fileName: string) => void;
  onOpenWorkspace: (offerId: number) => void;
  isExpanded: boolean;
  onToggleExpand: () => void;
};

type OffersTableProps = {
  offers: RequestDetailsOffer[];
  statusMap: Record<number, OfferDecisionStatus>;
  acceptedOfferId?: number | null;
  isLoading?: boolean;
  errorMessage?: string | null;
  statusOptions: OfferStatusOption[];
  onStatusChange: (offerId: number, value: OfferDecisionStatus) => void;
  onOpenWorkspace: (offerId: number) => void;
  onDownloadFile: (downloadUrl: string, fileName: string) => void;
  canChangeStatus?: boolean;
  onAddClick?: () => void;
};

type NotificationStyle = {
  borderColor: string;
  icon: ReactNode;
};

const getFileLabelWithHint = (value: string, max = 24) => {
  if (value.length <= max) {
    return value;
  }

  const extIndex = value.lastIndexOf('.');
  const hasExtension = extIndex > 0 && extIndex < value.length - 1;
  const extension = hasExtension ? value.slice(extIndex) : '';
  const base = hasExtension ? value.slice(0, extIndex) : value;
  const maxBase = Math.max(8, max - extension.length - 3);

  return `${base.slice(0, maxBase)}...${extension}`;
};

const getCounterpartyInfo = (offer: RequestDetailsOffer) => {
  const inn = offer.contractor_inn ?? null;
  const companyName = offer.contractor_company_name ?? null;
  const companyPhone = offer.contractor_company_phone ?? offer.contractor_phone ?? null;
  const companyMail = offer.contractor_company_mail ?? offer.contractor_mail ?? null;
  const companyAddress = offer.contractor_address ?? null;
  const companyNote = offer.contractor_note ?? null;

  return [
    `ИНН: ${inn ?? 'Не указано'}`,
    `Наименование компании: ${companyName ?? 'Не указано'}`,
    `Телефон: ${companyPhone ?? 'Не указано'}`,
    `E-mail: ${companyMail ?? 'Не указано'}`,
    `Адрес: ${companyAddress ?? 'Не указано'}`,
    `Дополнительная информация: ${companyNote ?? 'Не указано'}`
  ];
};

const getContactPersonInfo = (offer: RequestDetailsOffer) => {
  const fullName = offer.contractor_full_name ?? null;
  const phone = offer.contractor_contact_phone ?? offer.contractor_phone ?? null;
  const mail = offer.contractor_contact_mail ?? offer.contractor_mail ?? null;
  return [
    `ФИО: ${fullName ?? 'Не указано'}`,
    `Телефон: ${phone ?? 'Не указано'}`,
    `E-mail: ${mail ?? 'Не указано'}`
  ];
};

const getNotificationStyle = (status: string | null, palette: { divider: string; text: string }): NotificationStyle => {
  if (status === 'accepted') {
    return {
      borderColor: '#1976d2',
      icon: <CheckCircleOutlineIcon fontSize="small" sx={{ color: '#1976d2' }} />
    };
  }

  if (status === 'submitted') {
    return {
      borderColor: '#2e7d32',
      icon: <AccessTimeOutlinedIcon sx={{ color: '#2e7d32', fontSize: 24 }} />
    };
  }

  if (status === 'deleted') {
    return {
      borderColor: '#c62828',
      icon: <ReportProblemOutlinedIcon fontSize="small" sx={{ color: '#c62828' }} />
    };
  }

  if (status === 'rejected') {
    return {
      borderColor: '#787878',
      icon: <HighlightOffOutlinedIcon fontSize="small" sx={{ color: '#787878' }} />
    };
  }

  return {
    borderColor: palette.divider,
    icon: <RemoveOutlinedIcon fontSize="small" sx={{ color: palette.text }} />
  };
};

const getUnreadMessagesLabel = (count: number) => {
  if (count <= 0) {
    return null;
  }
  if (count === 1) {
    return 'Новое сообщение';
  }
  return `Новых сообщений: ${count}`;
};

const getOfferStatusLabel = (status: string | null) => {
  if (status === 'accepted') {
    return 'Принято';
  }
  if (status === 'submitted') {
    return 'На рассмотрении';
  }
  if (status === 'deleted') {
    return 'Удалено';
  }
  if (status === 'rejected') {
    return 'Отказано';
  }
  return 'Неизвестный статус';
};

const OfferMobileCard = ({
  offer,
  selectedStatus,
  statusOptions,
  acceptedOfferId,
  canChangeStatus,
  onStatusChange,
  onDownloadFile,
  onOpenWorkspace,
  isExpanded,
  onToggleExpand
}: OfferMobileCardProps) => {
  const theme = useTheme();
  const notificationStyle = getNotificationStyle(offer.status, {
    divider: theme.palette.divider,
    text: theme.palette.text.primary
  });
  const statusLabel = getOfferStatusLabel(offer.status ?? null);
  const detailRows = [
    {
      label: 'Контрагент',
      content: (
        <Stack spacing={0.35}>
          {getCounterpartyInfo(offer).map((line) => (
            <Typography key={`ctr-${offer.offer_id}-${line}`} variant="body2">
              {line}
            </Typography>
          ))}
        </Stack>
      )
    },
    {
      label: 'Контактное лицо',
      content: (
        <Stack spacing={0.35}>
          {getContactPersonInfo(offer).map((line) => (
            <Typography key={`contact-${offer.offer_id}-${line}`} variant="body2">
              {line}
            </Typography>
          ))}
        </Stack>
      )
    },
    {
      label: 'Дата создания',
      content: <Typography variant="body2">{formatDate(offer.created_at)}</Typography>
    },
    {
      label: 'Дата изменения',
      content: <Typography variant="body2">{formatDate(offer.updated_at)}</Typography>
    },
    {
      label: 'КП',
      content:
        offer.files.length > 0 ? (
          <Stack direction="row" flexWrap="wrap" gap={0.7}>
            {offer.files.map((file) => (
              <Tooltip key={`card-file-${file.id}`} title={file.name} arrow>
                <Chip
                  label={getFileLabelWithHint(file.name)}
                  variant="outlined"
                  size="small"
                  sx={{
                    borderRadius: 999,
                    bgcolor: 'background.paper',
                    cursor: 'pointer',
                    maxWidth: '100%',
                    '& .MuiChip-label': {
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }
                  }}
                  onClick={(event) => {
                    event.stopPropagation();
                    void onDownloadFile(file.download_url, file.name);
                  }}
                />
              </Tooltip>
            ))}
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary">
            -
          </Typography>
        )
    }
  ];

  const unreadLabel = getUnreadMessagesLabel(offer.unread_messages_count ?? 0);
  const handleToggleExpand = (event: ReactMouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    onToggleExpand();
  };

  return (
    <Paper
      onClick={() => onOpenWorkspace(offer.offer_id)}
      sx={{
        p: { xs: 1.25, sm: 1.5 },
        borderRadius: `${theme.acomShape.controlRadius}px`,
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
        cursor: 'pointer',
        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
        boxShadow: `0 2px 8px ${alpha(theme.palette.common.black, 0.04)}`,
        '&:hover': {
          borderColor: 'primary.main',
          boxShadow: `0 6px 14px ${alpha(theme.palette.common.black, 0.08)}`
        }
      }}
    >
      <Stack spacing={1.1}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" gap={1.25}>
          <Stack sx={{ minWidth: 0, gap: 0.2 }}>
            <Typography
              sx={{
                minWidth: 0,
                fontSize: 16,
                fontWeight: 600,
                color: 'text.primary',
                whiteSpace: 'normal',
                wordBreak: 'break-word'
              }}
            >
              {offer.contractor_company_name ?? offer.contractor_full_name ?? `КП №${offer.offer_id}`}
            </Typography>
            <Typography sx={{ fontSize: 14, color: 'text.secondary' }}>{`КП №${offer.offer_id}`}</Typography>
          </Stack>

          <Stack
            onClick={(event: ReactMouseEvent<HTMLDivElement>) => event.stopPropagation()}
            onMouseDown={(event: ReactMouseEvent<HTMLDivElement>) => event.stopPropagation()}
            sx={{ minWidth: 124, flexShrink: 0 }}
          >
            <Select
              size="small"
              value={selectedStatus}
              displayEmpty
              onChange={(event) => onStatusChange(offer.offer_id, event.target.value as OfferDecisionStatus)}
              disabled={!canChangeStatus || offer.status === 'deleted' || (!offer.actions.accept && !offer.actions.reject)}
              sx={{ minWidth: 124 }}
            >
              <MenuItem value="">
                <Typography variant="body2" color="text.secondary">
                  Выберите
                </Typography>
              </MenuItem>
              {statusOptions.map((option) => {
                const isAcceptedBlocked =
                  option.value === 'accepted'
                  && (Boolean(acceptedOfferId) && acceptedOfferId !== offer.offer_id || !offer.actions.accept);
                const isRejectedBlocked = option.value === 'rejected' && !offer.actions.reject;
                return (
                  <MenuItem
                    key={`card-status-${offer.offer_id}-${option.value}`}
                    value={option.value}
                    disabled={isAcceptedBlocked || isRejectedBlocked}
                  >
                    {option.label}
                  </MenuItem>
                );
              })}
            </Select>
          </Stack>
        </Stack>

        <Stack direction="row" alignItems="center" justifyContent="space-between" gap={1}>
          <Stack direction="row" alignItems="center" gap={0.75}>
            <Tooltip title={statusLabel} enterTouchDelay={0}>
              <Box
                sx={{
                  width: 28,
                  height: 28,
                  borderRadius: 8,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                {notificationStyle.icon}
              </Box>
            </Tooltip>
            <Typography sx={{ fontSize: 18, fontWeight: 600, color: 'text.primary', lineHeight: 1.15 }}>
              {formatAmount(offer.offer_amount)}
            </Typography>
          </Stack>
          {unreadLabel ? (
            <StatusPill
              label=""
              tone="info"
              icon={<MarkEmailUnreadRounded sx={{ fontSize: 15 }} />}
              iconOnly
            />
          ) : null}
        </Stack>

        <Stack direction="row" justifyContent="flex-end">
          <ButtonBase
            onClick={handleToggleExpand}
            sx={{
              px: 0.5,
              py: 0.25,
              borderRadius: `${theme.acomShape.controlRadius}px`,
              color: 'text.secondary',
              transition: 'color 0.2s ease, background-color 0.2s ease',
              '&:hover': {
                color: 'primary.main',
                bgcolor: alpha(theme.palette.primary.main, 0.06)
              }
            }}
          >
            <Stack direction="row" alignItems="center" gap={0.25}>
              <Typography sx={{ fontSize: 16, fontWeight: 500 }}>
                {isExpanded ? 'Свернуть' : 'Подробнее'}
              </Typography>
              <ExpandMoreRounded
                sx={{
                  fontSize: 22,
                  transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.26s ease'
                }}
              />
            </Stack>
          </ButtonBase>
        </Stack>

        <Collapse in={isExpanded} timeout={{ enter: 300, exit: 220 }} unmountOnExit>
          <Stack divider={<Divider flexItem />}>
            {detailRows.map((item) => (
              <Stack key={`card-detail-${offer.offer_id}-${item.label}`} sx={{ py: 0.75 }}>
                <Stack direction="row" alignItems="flex-start" gap={1.1} sx={{ minWidth: 0 }}>
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
                    {item.label}
                  </Typography>
                  <Stack sx={{ minWidth: 0, flex: 1 }}>{item.content}</Stack>
                </Stack>
              </Stack>
            ))}
          </Stack>
        </Collapse>
      </Stack>
    </Paper>
  );
};

export const OffersTable = ({
  offers,
  statusMap,
  acceptedOfferId,
  isLoading,
  errorMessage,
  statusOptions,
  onStatusChange,
  onOpenWorkspace,
  onDownloadFile,
  canChangeStatus = true,
  onAddClick
}: OffersTableProps) => {
  const theme = useTheme();
  const [expandedCardsById, setExpandedCardsById] = useState<Record<number, boolean>>({});
  const statusContent = errorMessage ? <Typography color="error">{errorMessage}</Typography> : null;
  const notificationPalette = {
    divider: theme.palette.divider,
    text: theme.palette.text.primary
  };
  const statusFilterOptions = statusOptions.map((option) => ({ label: option.label, value: option.label }));
  const areAllCardsExpanded = offers.length > 0 && offers.every((offer) => Boolean(expandedCardsById[offer.offer_id]));

  const handleToggleOfferCardExpand = (offerId: number) => {
    setExpandedCardsById((currentState) => ({
      ...currentState,
      [offerId]: !currentState[offerId]
    }));
  };

  const handleToggleAllOfferCards = (checked: boolean) => {
    setExpandedCardsById(
      Object.fromEntries(offers.map((offer) => [offer.offer_id, checked])) as Record<number, boolean>
    );
  };

  const columns: TableTemplateColumn<RequestDetailsOffer>[] = [
    {
      id: 'status',
      header: '',
      minWidth: 56,
      width: '56px',
      align: 'center',
      sortable: false,
      renderCell: (offer) => {
        const notificationStyle = getNotificationStyle(offer.status, notificationPalette);
        const statusLabel = getOfferStatusLabel(offer.status ?? null);
        return (
          <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
            <Tooltip title={statusLabel} enterTouchDelay={0}>
              <Box
                sx={{
                  width: 28,
                  height: 28,
                  borderRadius: 8,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'transparent',
                  fontWeight: 700
                }}
              >
                {notificationStyle.icon}
              </Box>
            </Tooltip>
          </Box>
        );
      }
    },
    {
      id: 'offerAmount',
      header: 'Сумма КП',
      field: 'offer_amount',
      minWidth: 150,
      renderValue: (value) => <Typography variant="body2">{formatAmount(value as number | null | undefined)}</Typography>
    },
    {
      id: 'offerId',
      header: 'Номер КП',
      field: 'offer_id',
      minWidth: 82,
      width: '90px',
      renderValue: (value) => <Typography variant="body2" fontWeight={600}>{String(value ?? '-')}</Typography>
    },
    {
      id: 'counterparty',
      header: 'Контрагент',
      minWidth: 260,
      width: '1.4fr',
      getSearchValue: (offer) => getCounterpartyInfo(offer).join(' '),
      renderCell: (offer) => {
        const counterpartyInfo = getCounterpartyInfo(offer);
        return (
          <Stack spacing={0.5}>
            {counterpartyInfo.map((item) => (
              <Typography key={item} variant="body2">
                {item}
              </Typography>
            ))}
          </Stack>
        );
      }
    },
    {
      id: 'contacts',
      header: 'Контактное лицо',
      minWidth: 240,
      width: '1.2fr',
      getSearchValue: (offer) => getContactPersonInfo(offer).join(' '),
      renderCell: (offer) => {
        const contactPersonInfo = getContactPersonInfo(offer);
        return (
          <Stack spacing={0.5}>
            {contactPersonInfo.map((item) => (
              <Typography key={item} variant="body2">
                {item}
              </Typography>
            ))}
          </Stack>
        );
      }
    },
    {
      id: 'createdAt',
      header: 'Дата создания',
      field: 'created_at',
      minWidth: 96,
      width: '108px',
      renderValue: (value) => <Typography variant="body2">{formatDate(value as string | null)}</Typography>
    },
    {
      id: 'updatedAt',
      header: 'Дата изменения',
      field: 'updated_at',
      minWidth: 96,
      width: '108px',
      renderValue: (value) => <Typography variant="body2">{formatDate(value as string | null)}</Typography>
    },
    {
      id: 'file',
      header: 'КП',
      field: 'files',
      minWidth: 170,
      width: '1.05fr',
      renderCell: (offer) =>
        offer.files.length > 0 ? (
          <Stack direction="row" flexWrap="wrap" gap={0.7}>
            {offer.files.map((file) => (
              <Tooltip key={file.id} title={file.name} arrow>
                <Chip
                  label={getFileLabelWithHint(file.name)}
                  variant="outlined"
                  size="small"
                  sx={{
                    borderRadius: 999,
                    backgroundColor: '#fff',
                    cursor: 'pointer',
                    maxWidth: 180,
                    '& .MuiChip-label': {
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }
                  }}
                  onClick={(event) => {
                    event.stopPropagation();
                    void onDownloadFile(file.download_url, file.name);
                  }}
                />
              </Tooltip>
            ))}
          </Stack>
        ) : (
          <Typography variant="body2">-</Typography>
        )
    },
    {
      id: 'statusSelect',
      header: 'Статус',
      minWidth: 214,
      width: '220px',
      filterKind: 'select',
      filterOptions: statusFilterOptions,
      getFilterValue: (offer) => {
        const selected = statusMap[offer.offer_id] ?? '';
        return statusOptions.find((item) => item.value === selected)?.label ?? 'Выберите';
      },
      getSearchValue: (offer) => {
        const selected = statusMap[offer.offer_id] ?? '';
        return statusOptions.find((item) => item.value === selected)?.label ?? '';
      },
      renderCell: (offer) => {
        const currentStatus = statusMap[offer.offer_id] ?? '';
        return (
          <Select
            size="small"
            value={currentStatus}
            displayEmpty
            onChange={(event) => onStatusChange(offer.offer_id, event.target.value as OfferDecisionStatus)}
            onClick={(event) => event.stopPropagation()}
            disabled={!canChangeStatus || offer.status === 'deleted' || (!offer.actions.accept && !offer.actions.reject)}
            sx={{ width: '100%', minWidth: 198 }}
          >
            <MenuItem value="">
              <Typography variant="body2" color="text.secondary">
                Выберите
              </Typography>
            </MenuItem>
            {statusOptions.map((option) => {
              const isAcceptedBlocked =
                option.value === 'accepted'
                && (Boolean(acceptedOfferId) && acceptedOfferId !== offer.offer_id || !offer.actions.accept);
              const isRejectedBlocked = option.value === 'rejected' && !offer.actions.reject;
              return (
                <MenuItem key={option.value} value={option.value} disabled={isAcceptedBlocked || isRejectedBlocked}>
                  {option.label}
                </MenuItem>
              );
            })}
          </Select>
        );
      }
    },
    {
      id: 'communication',
      header: 'Общение',
      minWidth: 118,
      width: '128px',
      renderCell: (offer) => {
        const unreadCount = offer.unread_messages_count ?? 0;
        const unreadLabel = getUnreadMessagesLabel(unreadCount);
        if (!unreadLabel) {
          return (
            <Typography variant="body2" color="text.secondary">
              Откройте КП
            </Typography>
          );
        }
        return (
          <StatusPill
            label=""
            tone="info"
            icon={<MarkEmailUnreadRounded sx={{ fontSize: 15 }} />}
            iconOnly
          />
        );
      }
    }
  ];

  return (
    <TableTemplate
      columns={columns}
      rows={offers}
      getRowId={(offer) => offer.offer_id}
      isLoading={isLoading}
      statusContent={statusContent}
      noRowsLabel="КП пока не получены."
      searchPlaceholder="Найти КП"
      onRowClick={(offer) => onOpenWorkspace(offer.offer_id)}
      minTableWidth={1280}
      addButtonLabel="Внести КП вручную"
      onAddClick={onAddClick}
      renderCard={(offer) => (
        <OfferMobileCard
          offer={offer}
          selectedStatus={statusMap[offer.offer_id] ?? ''}
          statusOptions={statusOptions}
          acceptedOfferId={acceptedOfferId}
          canChangeStatus={canChangeStatus}
          onStatusChange={onStatusChange}
          onDownloadFile={onDownloadFile}
          onOpenWorkspace={onOpenWorkspace}
          isExpanded={Boolean(expandedCardsById[offer.offer_id])}
          onToggleExpand={() => handleToggleOfferCardExpand(offer.offer_id)}
        />
      )}
      cardExpansionControl={{
        checked: areAllCardsExpanded,
        onChange: handleToggleAllOfferCards,
        openLabel: 'Раскрыть все',
        closeLabel: 'Свернуть все'
      }}
      getCardPrimaryText={(offer) => offer.contractor_company_name ?? offer.contractor_full_name ?? `КП №${offer.offer_id}`}
      getCardSecondaryText={(offer) => `КП №${offer.offer_id}`}
      cardExcludedColumnIds={['status', 'statusSelect', 'communication']}
    />
  );
};
