import { zodResolver } from '@hookform/resolvers/zod';
import EditOutlined from '@mui/icons-material/EditOutlined';
import SaveOutlined from '@mui/icons-material/SaveOutlined';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogContent,
  FormControlLabel,
  FormGroup,
  InputBase,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useLiveValidatedForm } from '@shared/lib/forms';
import { z } from 'zod';
import type { UserListItem } from '@entities/user';
import {
  InfoRow,
  SourceSection,
  UserStatusPill,
  dialogContentSx,
  dialogPaperSx,
  normalizeUserStatus,
} from '@features/admin/components/UserCardPrimitives';
import {
  useContractorTableEditing,
  type ContractorEditField,
} from '@features/contractors/hooks/useContractorTableEditing';
import type { ContractorListItem } from '@shared/api/contractors/listContractors';
import {
  getContractorRootUnits,
  type ContractorRootUnitsResult,
} from '@shared/api/contractors/getContractorRootUnits';
import { updateContractorStatus } from '@shared/api/contractors/updateContractorStatus';
import { updateContractorRootUnits } from '@shared/api/contractors/updateContractorRootUnits';
import { TableTemplate, type TableTemplateColumn } from '@shared/components/TableTemplate';
import { useSystemToasts } from '@shared/ui/toasts';
import { ContractorMobileCard } from './ContractorMobileCard';
import { ContractorUnitsCell } from './ContractorUnitsCell';
import { ContractorEditableFieldFrame, ContractorReadOnlyFieldFrame } from './contractorFieldValidation';
import {
  ContractorStatusPill,
  ContractorTableCell,
  formatPhoneForView,
  statusLabelForFilter,
  statusMemoText,
} from './contractorUi';

const statusSchema = z.object({
  user_status: z.enum(['review', 'active', 'inactive', 'blacklist']),
});

type StatusFormValues = z.infer<typeof statusSchema>;

const VIEW_COLUMN_IDS = [
  'status',
  'units',
  'login',
  'full_name',
  'phone',
  'mail',
  'company_phone',
  'company_mail',
] as const;

const ALL_COLUMN_IDS = [
  ...VIEW_COLUMN_IDS,
  'company_name',
  'inn',
  'address',
  'note',
  'created_at',
  'updated_at',
] as const;

const toUserListItem = (row: ContractorListItem): UserListItem => ({
  user_id: row.userId,
  role_id: row.roleId,
  id_parent: null,
  status: row.status,
  full_name: row.fullName,
  phone: row.phone,
  mail: row.mail,
  company_name: row.companyName,
  inn: row.inn,
  company_phone: row.companyPhone,
  company_mail: row.companyMail,
  address: row.address,
  note: row.note,
  units_count: 0,
  managers_count: 0,
  subordinates_count: 0,
  actions: row.actions,
});

const formatDateTime = (value: string | null) => {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed);
};

export type ContractorsListViewProps = {
  contractors: ContractorListItem[];
  isLoading?: boolean;
  emptyMessage: string;
  onStatusUpdated: () => Promise<void>;
  onAddClick?: () => void;
};

export const ContractorsListView = ({
  contractors,
  isLoading = false,
  emptyMessage,
  onStatusUpdated,
  onAddClick,
}: ContractorsListViewProps) => {
  const theme = useTheme();
  const { showSystemToast, showErrorToast } = useSystemToasts();
  const [isEditMode, setIsEditMode] = useState(false);
  const [visibleColumnIds, setVisibleColumnIds] = useState<string[]>([...VIEW_COLUMN_IDS]);
  const [selectedUser, setSelectedUser] = useState<UserListItem | null>(null);
  const [selectedUserRootUnits, setSelectedUserRootUnits] = useState<ContractorRootUnitsResult | null>(null);
  const [rootUnitDraftById, setRootUnitDraftById] = useState<Record<number, boolean>>({});
  const [isLoadingRootUnits, setIsLoadingRootUnits] = useState(false);
  const [isSavingRootUnits, setIsSavingRootUnits] = useState(false);
  const [rootUnitsError, setRootUnitsError] = useState<string | null>(null);
  const [expandedContractorCardsById, setExpandedContractorCardsById] = useState<
    Record<string, { contact: boolean; company: boolean }>
  >({});

  const {
    dirtyRowCount,
    isSaving,
    updateDraftValue,
    handleCancel,
    handleSave,
    getDraft,
    getFieldError,
    isFieldDirty,
    getFieldValue,
  } = useContractorTableEditing({
    rows: contractors,
    isEditMode,
    onSaved: onStatusUpdated,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting },
  } = useLiveValidatedForm<StatusFormValues>({
    resolver: zodResolver(statusSchema),
    defaultValues: { user_status: 'review' },
  });

  useEffect(() => {
    if (!selectedUser) {
      return;
    }
    reset({ user_status: normalizeUserStatus(selectedUser.status) });
  }, [reset, selectedUser]);

  useEffect(() => {
    if (!selectedUser) {
      setSelectedUserRootUnits(null);
      setRootUnitDraftById({});
      setRootUnitsError(null);
      return;
    }

    let isCancelled = false;
    setIsLoadingRootUnits(true);
    setRootUnitsError(null);

    void getContractorRootUnits(selectedUser.user_id)
      .then((result) => {
        if (isCancelled) {
          return;
        }
        setSelectedUserRootUnits(result);
        setRootUnitDraftById(
          Object.fromEntries(result.items.map((item) => [item.unitId, item.isBound])),
        );
      })
      .catch((error) => {
        if (isCancelled) {
          return;
        }
        setSelectedUserRootUnits(null);
        setRootUnitDraftById({});
        setRootUnitsError(
          error instanceof Error ? error.message : 'Не удалось загрузить привязки к подразделениям',
        );
      })
      .finally(() => {
        if (!isCancelled) {
          setIsLoadingRootUnits(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [selectedUser]);

  const canEditContractorData = useMemo(
    () => contractors.some((row) => row.actions.manage_manual_contractor),
    [contractors],
  );

  const manageableRootUnitIds = useMemo(
    () => selectedUserRootUnits?.items.filter((item) => item.canManage).map((item) => item.unitId) ?? [],
    [selectedUserRootUnits],
  );

  const hasRootUnitChanges = useMemo(() => (
    selectedUserRootUnits?.items.some(
      (item) => item.canManage && rootUnitDraftById[item.unitId] !== item.isBound,
    ) ?? false
  ), [rootUnitDraftById, selectedUserRootUnits]);

  useEffect(() => {
    setVisibleColumnIds(isEditMode ? [...ALL_COLUMN_IDS] : [...VIEW_COLUMN_IDS]);
  }, [isEditMode]);

  useEffect(() => {
    if (!canEditContractorData && isEditMode) {
      handleCancel();
      setIsEditMode(false);
    }
  }, [canEditContractorData, isEditMode, handleCancel]);

  const handleEnterEditMode = () => {
    setIsEditMode(true);
  };

  const handleCancelEdits = () => {
    handleCancel();
    setIsEditMode(false);
  };

  const handleSaveEdits = async () => {
    await handleSave();
  };

  const contractorStatusFilterOptions = useMemo(
    () => Array.from(new Set(contractors.map((row) => statusLabelForFilter(row.status)))).map((status) => ({
      label: status,
      value: status,
    })),
    [contractors],
  );

  const renderLockedCell = useCallback((content: ReactNode) => {
    if (!isEditMode) {
      return content;
    }
    return <ContractorReadOnlyFieldFrame locked>{content}</ContractorReadOnlyFieldFrame>;
  }, [isEditMode]);

  const renderStatusField = useCallback((row: ContractorListItem) => {
    const draft = getDraft(row);
    const value = (draft.status as string | undefined) ?? getFieldValue(row, 'status');
    const dirty = isFieldDirty(row, 'status', draft);

    return (
      <ContractorEditableFieldFrame dirty={dirty}>
        <Select
          value={value}
          onChange={(event) => updateDraftValue(row, 'status', event.target.value)}
          disabled={isSaving}
          variant="standard"
          disableUnderline
          aria-label={`${row.userId}-status`}
          inputProps={{ 'aria-label': `${row.userId}-status` }}
          sx={{ width: '100%', fontSize: 14 }}
        >
          <MenuItem value="review">На проверке</MenuItem>
          <MenuItem value="active">Активен</MenuItem>
          <MenuItem value="inactive">Неактивен</MenuItem>
          <MenuItem value="blacklist">В черном списке</MenuItem>
        </Select>
      </ContractorEditableFieldFrame>
    );
  }, [getDraft, getFieldValue, isFieldDirty, isSaving, updateDraftValue]);

  const renderEditableField = useCallback((
    row: ContractorListItem,
    field: ContractorEditField,
    editable: boolean,
  ) => {
    const draft = getDraft(row);
    const value = (draft[field] as string | undefined) ?? getFieldValue(row, field);
    const error = getFieldError(row, field);
    const dirty = isFieldDirty(row, field, draft);

    if (!isEditMode || !editable) {
      const content = <ContractorTableCell value={value || null} />;

      if (isEditMode && !editable) {
        return <ContractorReadOnlyFieldFrame locked>{content}</ContractorReadOnlyFieldFrame>;
      }
      return content;
    }

    return (
      <ContractorEditableFieldFrame error={error} dirty={dirty}>
        <InputBase
          value={value}
          onChange={(event) => updateDraftValue(row, field, event.target.value)}
          disabled={isSaving}
          inputProps={{ 'aria-label': `${row.userId}-${field}` }}
          sx={{
            width: '100%',
            fontSize: 14,
            px: 0.25,
          }}
        />
      </ContractorEditableFieldFrame>
    );
  }, [
    getDraft,
    getFieldError,
    getFieldValue,
    isEditMode,
    isFieldDirty,
    isSaving,
    updateDraftValue,
  ]);

  const contractorColumnsTemplate = useMemo<TableTemplateColumn<ContractorListItem>[]>(
    () => [
      {
        id: 'status',
        header: 'Статус',
        minWidth: 150,
        filterKind: 'select',
        filterOptions: contractorStatusFilterOptions,
        getFilterValue: (row) => statusLabelForFilter(row.status),
        getSearchValue: (row) => statusLabelForFilter(row.status),
        getSortValue: (row) => statusLabelForFilter(row.status),
        renderCell: (row) => {
          if (!isEditMode) {
            return <ContractorStatusPill value={row.status} />;
          }
          return row.actions.update_status
            ? renderStatusField(row)
            : renderLockedCell(<ContractorStatusPill value={row.status} />);
        },
      },
      {
        id: 'units',
        header: 'Подразделения',
        minWidth: 190,
        sortable: false,
        renderCell: (row) => <ContractorUnitsCell contractor={row} onSaved={onStatusUpdated} />,
      },
      {
        id: 'login',
        header: 'Логин',
        field: 'userId',
        minWidth: 170,
        getSearchValue: (row) => row.userId,
        renderCell: (row) => renderLockedCell(<ContractorTableCell value={row.userId} />),
      },
      {
        id: 'full_name',
        header: 'ФИО',
        minWidth: 190,
        getSearchValue: (row) => row.fullName ?? '',
        getSortValue: (row) => row.fullName ?? '',
        renderCell: (row) => renderEditableField(row, 'full_name', row.actions.manage_manual_contractor),
      },
      {
        id: 'phone',
        header: 'Телефон',
        minWidth: 150,
        getSearchValue: (row) => formatPhoneForView(row.phone) ?? '',
        getSortValue: (row) => formatPhoneForView(row.phone) ?? '',
        renderCell: (row) => renderEditableField(row, 'phone', row.actions.manage_manual_contractor),
      },
      {
        id: 'mail',
        header: 'E-mail',
        minWidth: 190,
        getSearchValue: (row) => row.mail ?? '',
        getSortValue: (row) => row.mail ?? '',
        renderCell: (row) => renderEditableField(row, 'mail', row.actions.manage_manual_contractor),
      },
      {
        id: 'company_phone',
        header: 'Телефон компании',
        minWidth: 170,
        getSearchValue: (row) => formatPhoneForView(row.companyPhone) ?? '',
        getSortValue: (row) => formatPhoneForView(row.companyPhone) ?? '',
        renderCell: (row) => renderEditableField(row, 'company_phone', row.actions.manage_manual_contractor),
      },
      {
        id: 'company_mail',
        header: 'E-mail компании',
        minWidth: 190,
        getSearchValue: (row) => row.companyMail ?? '',
        getSortValue: (row) => row.companyMail ?? '',
        renderCell: (row) => renderEditableField(row, 'company_mail', row.actions.manage_manual_contractor),
      },
      {
        id: 'company_name',
        header: 'Компания',
        minWidth: 190,
        getSearchValue: (row) => row.companyName ?? '',
        getSortValue: (row) => row.companyName ?? '',
        renderCell: (row) => renderEditableField(row, 'company_name', row.actions.manage_manual_contractor),
      },
      {
        id: 'inn',
        header: 'ИНН',
        minWidth: 150,
        getSearchValue: (row) => row.inn ?? '',
        getSortValue: (row) => row.inn ?? '',
        renderCell: (row) => renderEditableField(row, 'inn', row.actions.manage_manual_contractor),
      },
      {
        id: 'address',
        header: 'Адрес',
        minWidth: 190,
        getSearchValue: (row) => row.address ?? '',
        getSortValue: (row) => row.address ?? '',
        renderCell: (row) => renderEditableField(row, 'address', row.actions.manage_manual_contractor),
      },
      {
        id: 'note',
        header: 'Примечание',
        minWidth: 200,
        sortable: false,
        getSearchValue: (row) => row.note ?? '',
        renderCell: (row) => renderEditableField(row, 'note', row.actions.manage_manual_contractor),
      },
      {
        id: 'created_at',
        header: 'Создан',
        minWidth: 165,
        getSortValue: (row) => row.createdAt ?? '',
        renderCell: (row) => renderLockedCell(<ContractorTableCell value={formatDateTime(row.createdAt)} />),
      },
      {
        id: 'updated_at',
        header: 'Обновлен',
        minWidth: 165,
        getSortValue: (row) => row.updatedAt ?? '',
        renderCell: (row) => renderLockedCell(<ContractorTableCell value={formatDateTime(row.updatedAt)} />),
      },
    ],
    [contractorStatusFilterOptions, isEditMode, onStatusUpdated, renderEditableField, renderLockedCell, renderStatusField],
  );

  const openContractorDetails = (row: ContractorListItem) => {
    setSelectedUser(toUserListItem(row));
  };

  const handleRootUnitToggle = (unitId: number, checked: boolean) => {
    setRootUnitDraftById((prev) => ({
      ...prev,
      [unitId]: checked,
    }));
  };

  const handleSaveRootUnits = async () => {
    if (!selectedUser || !selectedUserRootUnits) {
      return;
    }

    try {
      setIsSavingRootUnits(true);
      setRootUnitsError(null);
      const updated = await updateContractorRootUnits(
        selectedUser.user_id,
        manageableRootUnitIds.filter((unitId) => Boolean(rootUnitDraftById[unitId])),
      );
      setSelectedUserRootUnits(updated);
      setRootUnitDraftById(
        Object.fromEntries(updated.items.map((item) => [item.unitId, item.isBound])),
      );
      showSystemToast({
        severity: 'success',
        message: 'Привязки к подразделениям сохранены.',
      });
      await onStatusUpdated();
    } catch (error) {
      setRootUnitsError(
        error instanceof Error ? error.message : 'Не удалось сохранить привязки к подразделениям',
      );
    } finally {
      setIsSavingRootUnits(false);
    }
  };

  const handleStatusSubmit = async (values: StatusFormValues) => {
    if (!selectedUser) {
      return;
    }

    try {
      await updateContractorStatus(selectedUser.user_id, { user_status: values.user_status });
      showSystemToast({
        severity: 'success',
        message: 'Статус успешно обновлён.',
      });
      await onStatusUpdated();
      setSelectedUser((prev) =>
        prev
          ? {
              ...prev,
              status: values.user_status,
            }
          : prev,
      );
    } catch (error) {
      showErrorToast(error instanceof Error ? error.message : 'Не удалось обновить статус');
    }
  };

  return (
    <>
      <TableTemplate
        columns={contractorColumnsTemplate}
        rows={contractors}
        getRowId={(row) => row.userId}
        isLoading={isLoading || isSaving}
        noRowsLabel={emptyMessage}
        searchPlaceholder="Найти контрагента"
        addButtonLabel="Добавить контрагента"
        onAddClick={onAddClick}
        showAddAction={Boolean(onAddClick)}
        showViewToggle={!isEditMode}
        lockViewMode={isEditMode ? 'table' : undefined}
        minTableWidth={980}
        reorderableColumns
        defaultColumnOrder={[...ALL_COLUMN_IDS]}
        initialVisibleColumnIds={[...VIEW_COLUMN_IDS]}
        visibleColumnIds={visibleColumnIds}
        onVisibleColumnIdsChange={setVisibleColumnIds}
        toolbarBeforeAddActions={canEditContractorData ? (
          isEditMode ? (
          <Stack direction="row" spacing={1} alignItems="center">
            <Button
              variant="outlined"
              onClick={handleCancelEdits}
              disabled={isSaving}
              sx={{ textTransform: 'none', minHeight: 44, borderRadius: `${theme.acomShape.controlRadius}px` }}
            >
              Отменить
            </Button>
            <Button
              variant="contained"
              onClick={() => void handleSaveEdits()}
              disabled={dirtyRowCount === 0 || isSaving}
              startIcon={<SaveOutlined fontSize="small" />}
              sx={{
                textTransform: 'none',
                minHeight: 44,
                minWidth: 150,
                boxShadow: 'none',
                borderRadius: `${theme.acomShape.controlRadius}px`,
              }}
            >
              {isSaving ? 'Сохранение...' : 'Сохранить'}
            </Button>
          </Stack>
        ) : (
          <Button
            variant="outlined"
            onClick={handleEnterEditMode}
            startIcon={<EditOutlined fontSize="small" />}
            sx={{
              textTransform: 'none',
              minHeight: 44,
              flexShrink: 0,
              borderRadius: `${theme.acomShape.controlRadius}px`,
            }}
          >
            Редактировать
          </Button>
          )
        ) : undefined}
        cardExpansionControl={{
          checked:
            contractors.length > 0
            && contractors.every(
              (row) =>
                Boolean(expandedContractorCardsById[row.userId]?.contact)
                && Boolean(expandedContractorCardsById[row.userId]?.company),
            ),
          onChange: (checked) => {
            setExpandedContractorCardsById(
              Object.fromEntries(
                contractors.map((row) => [
                  row.userId,
                  {
                    contact: checked,
                    company: checked,
                  },
                ]),
              ),
            );
          },
          openLabel: 'Развернуть все',
          closeLabel: 'Свернуть все',
        }}
        getCardPrimaryText={(row) => row.companyName ?? row.fullName ?? row.userId}
        getCardSecondaryText={(row) => row.userId}
        cardExcludedColumnIds={['login']}
        renderCard={(row) => {
          const userRow = toUserListItem(row);
          return (
            <ContractorMobileCard
              row={userRow}
              isContactExpanded={Boolean(expandedContractorCardsById[row.userId]?.contact)}
              isCompanyExpanded={Boolean(expandedContractorCardsById[row.userId]?.company)}
              onToggleContact={() =>
                setExpandedContractorCardsById((prev) => ({
                  ...prev,
                  [row.userId]: {
                    contact: !prev[row.userId]?.contact,
                    company: Boolean(prev[row.userId]?.company),
                  },
                }))}
              onToggleCompany={() =>
                setExpandedContractorCardsById((prev) => ({
                  ...prev,
                  [row.userId]: {
                    contact: Boolean(prev[row.userId]?.contact),
                    company: !prev[row.userId]?.company,
                  },
                }))}
              onOpenDetails={() => openContractorDetails(row)}
            />
          );
        }}
        onRowClick={isEditMode ? undefined : openContractorDetails}
      />

      <Dialog
        open={Boolean(selectedUser)}
        onClose={() => setSelectedUser(null)}
        maxWidth="md"
        fullWidth
        aria-labelledby="contractor-card-dialog-title"
        PaperProps={{
          sx: dialogPaperSx,
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
                  backgroundColor: 'background.paper',
                }}
              >
                <Stack spacing={1.2}>
                  <SourceSection title="Пользователь" source="users">
                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                        gap: 1.5,
                      }}
                    >
                      <InfoRow label="Логин" value={selectedUser.user_id} />
                      <Stack spacing={0.2} sx={{ alignItems: 'flex-start' }}>
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{ textTransform: 'uppercase', letterSpacing: '0.04em' }}
                        >
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
                          gap: 1.2,
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
                          gap: 1.2,
                        }}
                      >
                        <InfoRow label="ИНН" value={selectedUser.inn} />
                        <InfoRow label="Компания" value={selectedUser.company_name} />
                      </Box>

                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                          gap: 1.2,
                        }}
                      >
                        <InfoRow label="Телефон компании" value={formatPhoneForView(selectedUser.company_phone)} />
                        <InfoRow label="E-mail компании" value={selectedUser.company_mail} />
                        <InfoRow label="Адрес" value={selectedUser.address} />
                      </Box>
                      <InfoRow label="Примечание" value={selectedUser.note} />
                    </Stack>
                  </SourceSection>

                  <SourceSection title="Подразделения" source="units">
                    <Stack spacing={1.2}>
                      {isLoadingRootUnits ? (
                        <Typography color="text.secondary">Загрузка привязок...</Typography>
                      ) : null}
                      {!isLoadingRootUnits && selectedUserRootUnits ? (
                        <FormGroup>
                          {selectedUserRootUnits.items.map((item) => (
                            <FormControlLabel
                              key={`${selectedUser.user_id}-${item.unitId}`}
                              control={(
                                <Checkbox
                                  checked={Boolean(rootUnitDraftById[item.unitId])}
                                  disabled={!item.canManage || isSavingRootUnits}
                                  onChange={(event) => handleRootUnitToggle(item.unitId, event.target.checked)}
                                />
                              )}
                              label={item.unitName}
                            />
                          ))}
                        </FormGroup>
                      ) : null}
                      {rootUnitsError ? <Alert severity="error">{rootUnitsError}</Alert> : null}
                      {selectedUser.actions.manage_contractor_unit_bindings && selectedUserRootUnits?.canManage ? (
                        <Stack direction="row" justifyContent="flex-end">
                          <Button
                            variant="outlined"
                            onClick={() => void handleSaveRootUnits()}
                            disabled={isSavingRootUnits || !hasRootUnitChanges}
                            sx={{ borderRadius: 1, textTransform: 'none' }}
                          >
                            {isSavingRootUnits ? 'Сохранение...' : 'Сохранить привязки'}
                          </Button>
                        </Stack>
                      ) : null}
                    </Stack>
                  </SourceSection>
                </Stack>
              </Box>

              {selectedUser.actions.update_status ? (
                <Stack
                  spacing={1.2}
                  sx={{
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    p: { xs: 1.4, sm: 1.8 },
                    backgroundColor: 'background.paper',
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
                          backgroundColor: 'background.paper',
                        },
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
                        <Typography variant="body2" sx={{ m: 0, whiteSpace: 'pre-line', lineHeight: 1.45 }}>
                          {statusMemoText}
                        </Typography>
                      }
                      slotProps={{
                        tooltip: {
                          sx: {
                            maxWidth: 380,
                            p: 1.4,
                            borderRadius: 2,
                          },
                        },
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
                          cursor: 'pointer',
                        }}
                      >
                        ?
                      </Box>
                    </Tooltip>
                  </Stack>

                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.2} justifyContent="flex-end">
                    <Button
                      variant="outlined"
                      onClick={() => setSelectedUser(null)}
                      sx={{ borderRadius: 1, textTransform: 'none' }}
                    >
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
              ) : null}
            </Stack>
          ) : null}
        </DialogContent>
      </Dialog>
    </>
  );
};
