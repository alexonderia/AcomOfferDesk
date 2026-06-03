import { zodResolver } from '@hookform/resolvers/zod';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogContent,
  MenuItem,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
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
import { updateContractorStatus } from '@shared/api/contractors/updateContractorStatus';
import { updateUserStatus } from '@shared/api/users/updateUserStatus';
import { TableTemplate, type TableTemplateColumn } from '@shared/components/TableTemplate';
import { useSystemToasts } from '@shared/ui/toasts';
import { ContractorMobileCard } from './ContractorMobileCard';
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

export type ContractorsListViewProps = {
  users: UserListItem[];
  isLoading?: boolean;
  emptyMessage: string;
  onStatusUpdated: () => Promise<void>;
  onAddClick?: () => void;
  useContractorsStatusApi?: boolean;
};

export const ContractorsListView = ({
  users,
  isLoading = false,
  emptyMessage,
  onStatusUpdated,
  onAddClick,
  useContractorsStatusApi = false,
}: ContractorsListViewProps) => {
  const { showSystemToast } = useSystemToasts();
  const [selectedUser, setSelectedUser] = useState<UserListItem | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [expandedContractorCardsById, setExpandedContractorCardsById] = useState<
    Record<string, { contact: boolean; company: boolean }>
  >({});

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
    setSubmitError(null);
  }, [reset, selectedUser]);

  const contractorStatusFilterOptions = useMemo(
    () => Array.from(new Set(users.map((user) => statusLabelForFilter(user.status)))).map((status) => ({
      label: status,
      value: status,
    })),
    [users]
  );

  const contractorColumnsTemplate = useMemo<TableTemplateColumn<UserListItem>[]>(
    () => [
      { id: 'login', header: 'Логин', field: 'user_id', minWidth: 170 },
      {
        id: 'full_name',
        header: 'ФИО',
        field: 'full_name',
        minWidth: 190,
        renderValue: (value) => <ContractorTableCell value={value as string | null} />,
      },
      {
        id: 'phone',
        header: 'Телефон',
        field: 'phone',
        minWidth: 150,
        renderValue: (value) => <ContractorTableCell value={formatPhoneForView(value as string | null)} />,
      },
      {
        id: 'mail',
        header: 'E-mail',
        field: 'mail',
        minWidth: 190,
        renderValue: (value) => <ContractorTableCell value={value as string | null} />,
      },
      {
        id: 'company_phone',
        header: 'Телефон компании',
        field: 'company_phone',
        minWidth: 170,
        renderValue: (value) => <ContractorTableCell value={formatPhoneForView(value as string | null)} />,
      },
      {
        id: 'company_mail',
        header: 'E-mail компании',
        field: 'company_mail',
        minWidth: 190,
        renderValue: (value) => <ContractorTableCell value={value as string | null} />,
      },
      {
        id: 'status',
        header: 'Статус',
        field: 'status',
        minWidth: 150,
        filterKind: 'select',
        filterOptions: contractorStatusFilterOptions,
        getFilterValue: (row) => statusLabelForFilter(row.status),
        getSearchValue: (row) => statusLabelForFilter(row.status),
        renderCell: (row) => <ContractorStatusPill value={row.status} />,
      },
    ],
    [contractorStatusFilterOptions]
  );

  const openContractorDetails = (user: UserListItem) => {
    setSelectedUser(user);
    setSubmitError(null);
  };

  const handleStatusSubmit = async (values: StatusFormValues) => {
    if (!selectedUser) {
      return;
    }
    setSubmitError(null);

    try {
      if (useContractorsStatusApi) {
        await updateContractorStatus(selectedUser.user_id, { user_status: values.user_status });
      } else {
        await updateUserStatus(selectedUser.user_id, { user_status: values.user_status });
      }
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
          : prev
      );
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'Не удалось обновить статус');
    }
  };

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
        showAddAction={Boolean(onAddClick)}
        minTableWidth={980}
        cardExpansionControl={{
          checked:
            users.length > 0
            && users.every(
              (row) =>
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
                    company: checked,
                  },
                ])
              )
            );
          },
          openLabel: 'Развернуть все',
          closeLabel: 'Свернуть все',
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
                  company: Boolean(prev[row.user_id]?.company),
                },
              }))
            }
            onToggleCompany={() =>
              setExpandedContractorCardsById((prev) => ({
                ...prev,
                [row.user_id]: {
                  contact: Boolean(prev[row.user_id]?.contact),
                  company: !prev[row.user_id]?.company,
                },
              }))
            }
            onOpenDetails={openContractorDetails}
          />
        )}
        onRowClick={openContractorDetails}
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

                  {submitError ? <Alert severity="error">{submitError}</Alert> : null}
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
