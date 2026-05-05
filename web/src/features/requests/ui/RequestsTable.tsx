import { MouseEvent as ReactMouseEvent, useState } from 'react';
import ExpandMoreRounded from '@mui/icons-material/ExpandMoreRounded';
import MarkEmailUnreadRounded from '@mui/icons-material/MarkEmailUnreadRounded';
import { Box, ButtonBase, Collapse, Divider, Paper, Select, Stack, Tooltip, Typography } from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import type { RequestWithOfferStats } from '@shared/api/requests/getRequests';
import { UnavailableAwareMenuItem } from '@shared/components/UnavailableAwareMenuItem';
import { StatusPill } from '@shared/components/StatusPill';
import { TableTemplate, type TableTemplateColumn } from '@shared/components/TableTemplate';
import type { UnavailabilityPeriodInfo } from '@shared/lib/unavailability';

type OwnerOption = {
    id: string;
    label: string;
    unavailablePeriod?: UnavailabilityPeriodInfo | null;
};

type RequestsTableProps = {
    requests: RequestWithOfferStats[];
    isLoading?: boolean;
    onRowClick?: (request: RequestWithOfferStats) => void;
    onAddClick?: () => void;
    chatAlertsMap?: Record<number, number>;
    ownerOptions?: OwnerOption[];
    canEditOwner?: boolean;
    onOwnerChange?: (request: RequestWithOfferStats, ownerUserId: string) => void;
    isContractor?: boolean;
    showContractorOffersColumn?: boolean;
    showContractorNotificationColumn?: boolean;
};

const requestStatusToneByValue: Record<string, 'success' | 'warning' | 'error' | 'info' | 'neutral'> = {
    open: 'success',
    review: 'warning',
    closed: 'neutral',
    canceled: 'neutral',
    cancelled: 'neutral'
};

type RequestTableRow = RequestWithOfferStats & {
    __notificationLabel: string;
    __statusLabel: string;
};

const capitalizeFirst = (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) {
        return '';
    }
    return `${trimmed.charAt(0).toUpperCase()}${trimmed.slice(1)}`;
};

const formatDate = (value: string | null, withTime = false) => {
    if (!value) {
        return '-';
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }

    const options: Intl.DateTimeFormatOptions = withTime
        ? {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }
        : {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        };

    return new Intl.DateTimeFormat('ru-RU', options).format(date);
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

const offerStatusToneKey: Record<string, keyof import('@mui/material/styles').StatusTones> = {
    submitted: 'success',
    accepted: 'info',
    rejected: 'neutral',
    deleted: 'error',
};

const offerStatusLabelMap: Record<string, string> = {
    submitted: 'На рассмотрении',
    accepted: 'Принято',
    rejected: 'Отклонено',
    deleted: 'Удалено',
};

const getContractorOfferStatusMeta = (status: string) => ({
    label: offerStatusLabelMap[status] ?? status
});

const NotificationContent = ({
    countSubmitted,
    countDeleted,
    countChatAlerts,
    unreadMessagesCount
}: {
    countSubmitted: number;
    countDeleted: number;
    countChatAlerts: number;
    unreadMessagesCount: number;
}) => {
    const hasUnreadMessages = unreadMessagesCount > 0;

    if (countSubmitted <= 0 && countDeleted <= 0 && countChatAlerts <= 0 && !hasUnreadMessages) {
        return null;
    }

    return (
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
            {countSubmitted > 0 ? (
                <StatusPill
                    label={countSubmitted === 1 ? 'Новое КП' : `${countSubmitted} новых КП`}
                    tone="success"
                />
            ) : null}
            {countDeleted > 0 ? (
                <StatusPill
                    label={countDeleted === 1 ? 'Отмена сделки' : `${countDeleted} отмены сделки`}
                    tone="error"
                />
            ) : null}
            {countChatAlerts > 0 ? (
                <StatusPill
                    label="Новый ответ"
                    tone="error"
                />
            ) : null}
            {hasUnreadMessages ? (
                <StatusPill
                    label=""
                    tone="info"
                    icon={<MarkEmailUnreadRounded sx={{ fontSize: 15 }} />}
                    iconOnly
                />
            ) : null}
        </Stack>
    );
};

type RequestMobileCardProps = {
    row: RequestTableRow;
    canEditOwner: boolean;
    isContractor: boolean;
    ownerOptions: OwnerOption[];
    onOwnerChange?: (request: RequestWithOfferStats, ownerUserId: string) => void;
    isExpanded: boolean;
    onToggleExpand: () => void;
    onOpenDetails?: (request: RequestWithOfferStats) => void;
};

const RequestMobileCard = ({
    row,
    canEditOwner,
    isContractor,
    ownerOptions,
    onOwnerChange,
    isExpanded,
    onToggleExpand,
    onOpenDetails
}: RequestMobileCardProps) => {
    const theme = useTheme();
    const descriptionText = row.description?.trim() ? row.description : '-';
    const ownerValue = row.owner_full_name ?? row.id_user;
    const detailRows = [
        { key: 'deadline', label: 'Прием КП до', value: formatDate(row.deadline_at) },
        { key: 'created', label: 'Открыта', value: formatDate(row.created_at) },
        { key: 'closed', label: 'Закрыта', value: formatDate(row.closed_at) },
        ...(!isContractor ? [{ key: 'offer', label: 'Номер КП', value: String(row.id_offer ?? '-') }] : []),
        { key: 'owner', label: 'Ответственный', value: ownerValue }
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
            <Stack spacing={1.25}>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start" gap={1.25}>
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
                        {`Заявка №${row.id}`}
                    </Typography>
                    <StatusPill
                        label={row.__statusLabel}
                        tone={requestStatusToneByValue[row.status ?? ''] ?? 'neutral'}
                    />
                </Stack>

                <Tooltip title={descriptionText} arrow placement="top-start" disableHoverListener={descriptionText.length <= 80}>
                    <Typography
                        sx={{
                            minHeight: 'calc(1.35em * 2)',
                            fontSize: 16,
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
                        {descriptionText}
                    </Typography>
                </Tooltip>

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
                                    transition: 'transform 0.28s ease'
                                }}
                            />
                        </Stack>
                    </ButtonBase>
                </Stack>

                <Divider />

                <Collapse in={isExpanded} timeout={{ enter: 300, exit: 220 }} unmountOnExit>
                    <Stack divider={<Divider flexItem />} spacing={0}>
                        {detailRows.map((detail) => {
                            const isOwnerDetail = detail.key === 'owner';
                            return (
                                <Stack key={`${row.id}-${detail.key}`} sx={{ py: 0.85 }}>
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
                                            {detail.label}
                                        </Typography>
                                        {isOwnerDetail && canEditOwner ? (
                                            <Stack
                                                onClick={(event: ReactMouseEvent<HTMLDivElement>) => event.stopPropagation()}
                                                onMouseDown={(event: ReactMouseEvent<HTMLDivElement>) => event.stopPropagation()}
                                                sx={{ minWidth: 0, flex: 1 }}
                                            >
                                                <Select
                                                    size="small"
                                                    value={row.id_user}
                                                    renderValue={(selected) =>
                                                        ownerOptions.find((option) => option.id === selected)?.label
                                                        ?? row.owner_full_name
                                                        ?? String(selected ?? '')
                                                    }
                                                    onChange={(event) => onOwnerChange?.(row, event.target.value)}
                                                    sx={{ minWidth: 120 }}
                                                >
                                                    {ownerOptions.map((option) => (
                                                        <UnavailableAwareMenuItem
                                                            key={`card-owner-${option.id}`}
                                                            value={option.id}
                                                            label={option.label}
                                                            unavailablePeriod={option.unavailablePeriod}
                                                        />
                                                    ))}
                                                </Select>
                                            </Stack>
                                        ) : (
                                            <Typography
                                                sx={{
                                                    minWidth: 0,
                                                    flex: 1,
                                                    fontSize: 15,
                                                    color: detail.value === '-' ? 'text.secondary' : 'text.primary',
                                                    whiteSpace: 'normal',
                                                    wordBreak: 'break-word'
                                                }}
                                            >
                                                {detail.value}
                                            </Typography>
                                        )}
                                    </Stack>
                                </Stack>
                            );
                        })}
                    </Stack>
                </Collapse>

                <Stack direction="row" justifyContent="space-between" alignItems="center" gap={1.25}>
                    <Box sx={{ minHeight: 28, display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                        {row.__notificationLabel === 'Есть уведомление' ? (
                            <StatusPill
                                label=""
                                tone="info"
                                icon={<MarkEmailUnreadRounded sx={{ fontSize: 15 }} />}
                                iconOnly
                            />
                        ) : null}
                    </Box>
                    <Typography
                        sx={{
                            minWidth: 0,
                            fontSize: 15,
                            color: 'text.secondary',
                            textAlign: 'right',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                        }}
                    >
                        {`обновлено ${formatDate(row.updated_at, true)}`}
                    </Typography>
                </Stack>
            </Stack>
        </Paper>
    );
};

export const RequestsTable = ({
    requests,
    isLoading,
    onRowClick,
    onAddClick,
    chatAlertsMap,
    ownerOptions = [],
    canEditOwner = false,
    onOwnerChange,
    isContractor = false,
    showContractorOffersColumn = true,
    showContractorNotificationColumn = true
}: RequestsTableProps) => {
    const [expandedCardsById, setExpandedCardsById] = useState<Record<number, boolean>>({});
    const rows = requests.map((request) => ({
        ...request,
        __notificationLabel: request.unread_messages_count && request.unread_messages_count > 0 ? 'Есть уведомление' : 'Нет уведомления',
        __statusLabel: capitalizeFirst(request.status_label ?? request.status ?? '-')
    }));
    const areAllCardsExpanded = rows.length > 0 && rows.every((row) => Boolean(expandedCardsById[row.id]));

    const handleToggleCardExpand = (rowId: number) => {
        setExpandedCardsById((currentState) => ({
            ...currentState,
            [rowId]: !currentState[rowId]
        }));
    };

    const handleToggleAllCards = (checked: boolean) => {
        setExpandedCardsById(
            Object.fromEntries(rows.map((row) => [row.id, checked])) as Record<number, boolean>
        );
    };
    const statusFilterOptions = Array.from(
        new Set(rows.map((row) => row.__statusLabel).filter((label) => Boolean(label)))
    ).map((label) => ({ label, value: label }));

    const ownerFilterOptions = Array.from(
        new Set(rows.map((row) => row.owner_full_name ?? row.id_user))
    ).map((label) => ({ label, value: label }));

    const columns: TableTemplateColumn<RequestTableRow>[] = [
        {
            id: 'id',
            header: 'ID',
            field: 'id',
            minWidth: 60,
            width: '72px',
            align: 'center',
            getSortValue: (row) => row.id
        },
        {
            id: 'description',
            header: 'Описание',
            field: 'description',
            minWidth: 230,
            width: '1.6fr',
            renderValue: (value) => {
                const text = String(value ?? '-');
                return (
                    <Tooltip title={text} arrow placement="top-start" disableHoverListener={text.trim().length <= 80}>
                        <Typography
                            component="span"
                            sx={{
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'normal',
                                wordBreak: 'break-word'
                            }}
                        >
                            {text}
                        </Typography>
                    </Tooltip>
                );
            }
        },
        {
            id: 'status',
            header: 'Статус',
            field: '__statusLabel',
            minWidth: 140,
            filterKind: 'select',
            filterOptions: statusFilterOptions,
            renderValue: (value, row) => (
                <StatusPill
                    label={String(value ?? '-')}
                    tone={requestStatusToneByValue[row.status ?? ''] ?? 'neutral'}
                />
            )
        },
        {
            id: 'deadline',
            header: 'Прием КП до',
            field: 'deadline_at',
            minWidth: 96,
            width: '104px',
            renderValue: (value) => <Typography variant="body2">{formatDate(value as string | null)}</Typography>
        },
        {
            id: 'created',
            header: 'Открыта',
            field: 'created_at',
            minWidth: 96,
            width: '104px',
            renderValue: (value) => <Typography variant="body2">{formatDate(value as string | null)}</Typography>
        },
        {
            id: 'closed',
            header: 'Закрыта',
            field: 'closed_at',
            minWidth: 96,
            width: '104px',
            renderValue: (value) => <Typography variant="body2">{formatDate(value as string | null)}</Typography>
        },
        {
            id: 'owner',
            header: 'Ответственный',
            minWidth: 240,
            width: '1.35fr',
            field: 'id_user',
            filterKind: 'select',
            filterOptions: ownerFilterOptions,
            getFilterValue: (row) => row.owner_full_name ?? row.id_user,
            getSearchValue: (row) => row.owner_full_name ?? row.id_user,
            renderCell: (row) =>
                canEditOwner ? (
                    <Select
                        size="small"
                        value={row.id_user}
                        renderValue={(selected) => ownerOptions.find((option) => option.id === selected)?.label ?? row.owner_full_name ?? String(selected ?? '')}
                        onClick={(event) => event.stopPropagation()}
                        onChange={(event) => onOwnerChange?.(row, event.target.value)}
                        sx={{ minWidth: 150 }}
                    >
                        {ownerOptions.map((option) => (
                            <UnavailableAwareMenuItem
                                key={option.id}
                                value={option.id}
                                label={option.label}
                                unavailablePeriod={option.unavailablePeriod}
                            />
                        ))}
                    </Select>
                ) : (
                    <Typography variant="body2">{row.owner_full_name ?? row.id_user}</Typography>
                )
        },
        {
            id: 'updated',
            header: 'Последнее обновление',
            field: 'updated_at',
            minWidth: 160,
            width: '170px',
            renderValue: (value) => <Typography variant="body2">{formatDate(value as string | null, true)}</Typography>
        }
    ];

    if (!isContractor) {
        columns.push({
            id: 'offer',
            header: 'Номер КП',
            field: 'id_offer',
            minWidth: 90,
            width: '96px',
            align: 'left',
            renderValue: (value) => <Typography variant="body2">{String(value ?? '-')}</Typography>
        });
    }

    if (isContractor && showContractorOffersColumn) {
        columns.push({
            id: 'contractorOffers',
            header: 'Мои отклики',
            field: 'offers',
            minWidth: 220,
            width: '1.3fr',
            renderCell: (row) => {
                const contractorOffers = row.offers ?? [];
                if (contractorOffers.length === 0) {
                    return <Typography variant="body2">-</Typography>;
                }
                return (
                    <Stack spacing={0.75} alignItems="flex-start">
                        {contractorOffers.map((offer) => {
                            const statusMeta = getContractorOfferStatusMeta(offer.status);
                            const statusTone = offerStatusToneKey[offer.status] ?? 'neutral';
                            return (
                                <StatusPill
                                    key={offer.id}
                                    label={`КП № ${offer.id} ${statusMeta.label}`}
                                    tone={statusTone}
                                />
                            );
                        })}
                    </Stack>
                );
            }
        });
    }

    if (!isContractor || showContractorNotificationColumn) {
        columns.push({
            id: 'notification',
            header: 'Уведомление',
            field: '__notificationLabel',
            minWidth: 180,
            width: '1.2fr',
            filterKind: 'select',
            filterOptions: [
                { label: 'Есть уведомление', value: 'Есть уведомление' },
                { label: 'Нет уведомления', value: 'Нет уведомления' }
            ],
            renderCell: (row) => {
                if (isContractor) {
                    const contractorOffers = row.offers ?? [];
                    const unreadCount = contractorOffers.reduce((acc, offer) => acc + (offer.unread_messages_count ?? 0), 0);
                    const unreadLabel = getUnreadMessagesLabel(unreadCount);
                    return unreadLabel ? (
                        <StatusPill
                            label=""
                            tone="info"
                            icon={<MarkEmailUnreadRounded sx={{ fontSize: 15 }} />}
                            iconOnly
                        />
                    ) : (
                        <Typography variant="body2" color="text.secondary">-</Typography>
                    );
                }
                return (
                    <NotificationContent
                        countSubmitted={row.count_submitted ?? 0}
                        countDeleted={row.count_deleted_alert ?? 0}
                        countChatAlerts={chatAlertsMap?.[row.id] ?? row.count_chat_alert ?? 0}
                        unreadMessagesCount={row.unread_messages_count ?? 0}
                    />
                );
            }
        });
    }

    return (
        <TableTemplate
            key={[
                showContractorOffersColumn ? 'offers-visible' : 'offers-hidden',
                showContractorNotificationColumn ? 'notifications-visible' : 'notifications-hidden'
            ].join(':')}
            columns={columns}
            rows={rows}
            getRowId={(row) => row.id}
            isLoading={isLoading}
            noRowsLabel="Заявки не найдены."
            onRowClick={onRowClick}
            minTableWidth={1160}
            searchPlaceholder="Найти заявку"
            addButtonLabel="Создать заявку"
            onAddClick={isContractor ? undefined : onAddClick}
            renderCard={(row) => (
                <RequestMobileCard
                    row={row}
                    canEditOwner={!isContractor && canEditOwner}
                    isContractor={isContractor}
                    ownerOptions={ownerOptions}
                    onOwnerChange={onOwnerChange}
                    isExpanded={Boolean(expandedCardsById[row.id])}
                    onToggleExpand={() => handleToggleCardExpand(row.id)}
                    onOpenDetails={onRowClick}
                />
            )}
            cardExpansionControl={{
                checked: areAllCardsExpanded,
                onChange: handleToggleAllCards,
                openLabel: 'Раскрыть все',
                closeLabel: 'Свернуть все'
            }}
        />
    );
};
