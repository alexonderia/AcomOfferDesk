import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import {
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  FormGroup,
  IconButton,
  InputAdornment,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useEffect, useState } from 'react';
import { useAuth } from '@app/providers/AuthProvider';
import { mapUserListItemToContractorListItem } from '@features/contractors/lib/mapUserListItemToContractorListItem';
import {
  listContractorsTable,
  type ContractorListItem,
} from '@shared/api/contractors/listContractors';
import { getContractorRootUnits } from '@shared/api/contractors/getContractorRootUnits';
import { getUsers } from '@shared/api/users/getUsers';
import { hasPermission } from '@shared/auth/permissions';
import { ROLE } from '@shared/constants/roles';
import { updateContractorRootUnits } from '@shared/api/contractors/updateContractorRootUnits';
import { useSystemToasts, useToastMessageEffect } from '@shared/ui/toasts';
import { hierarchyPageColors } from './unitHierarchyStyles';

const CONTRACTOR_FETCH_LIMIT = 100;

type DraftsById = Record<string, Record<number, boolean>>;

type ContractorBindingsDialogProps = {
  open: boolean;
  departmentName?: string | undefined;
  onClose: () => void;
  onSaved: () => Promise<void> | void;
};

const buildDrafts = (rows: ContractorListItem[]): DraftsById =>
  Object.fromEntries(
    rows.map((row) => [
      row.userId,
      Object.fromEntries((row.rootUnits?.items ?? []).map((item) => [item.unitId, item.isBound])),
    ]),
  );

const buildContractorLabel = (row: ContractorListItem) => {
  const company = row.companyName?.trim();
  const fullName = row.fullName?.trim();
  return { login: row.userId, fullName: fullName || null, company: company || null };
};

const matchesContractorSearch = (row: ContractorListItem, normalizedSearch: string) => {
  if (!normalizedSearch) {
    return true;
  }

  const haystack = [
    row.userId,
    row.fullName ?? '',
    row.companyName ?? '',
    row.mail ?? '',
  ].join(' ').toLocaleLowerCase('ru');

  return haystack.includes(normalizedSearch);
};

export const ContractorBindingsDialog = ({
  open,
  departmentName,
  onClose,
  onSaved,
}: ContractorBindingsDialogProps) => {
  const { session } = useAuth();
  const { showSystemToast, showErrorToast } = useSystemToasts();
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [rows, setRows] = useState<ContractorListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draftsById, setDraftsById] = useState<DraftsById>({});
  const [savingId, setSavingId] = useState<string | null>(null);
  const [isSavingAll, setIsSavingAll] = useState(false);

  useToastMessageEffect({ message: error });

  useEffect(() => {
    const handle = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(handle);
  }, [search]);

  useEffect(() => {
    if (!open) {
      setSearch('');
      setDebouncedSearch('');
      setRows([]);
      setDraftsById({});
      setError(null);
      setSavingId(null);
      setIsSavingAll(false);
    }
  }, [open]);

  useEffect(() => {
    if (!open) {
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    const normalizedSearch = debouncedSearch.toLocaleLowerCase('ru');
    const loadRows = hasPermission(session, 'contractors.read')
      ? listContractorsTable({
          search: debouncedSearch || undefined,
          limit: CONTRACTOR_FETCH_LIMIT,
        }).then((result) => result.items)
      : getUsers(ROLE.CONTRACTOR)
          .then(async (result) => {
            const filteredItems = result.items
              .map(mapUserListItemToContractorListItem)
              .filter((item) => matchesContractorSearch(item, normalizedSearch))
              .slice(0, CONTRACTOR_FETCH_LIMIT);

            const rootUnitsByUserId = new Map(
              await Promise.all(
                filteredItems.map(async (item) => [item.userId, await getContractorRootUnits(item.userId)] as const)
              )
            );

            return filteredItems.map((item) => ({
              ...item,
              rootUnits: rootUnitsByUserId.get(item.userId) ?? null,
            }));
          });

    void loadRows
      .then((result) => {
        if (cancelled) {
          return;
        }
        setRows(result);
        setDraftsById(buildDrafts(result));
      })
      .catch((loadError) => {
        if (cancelled) {
          return;
        }
        setRows([]);
        setError(loadError instanceof Error ? loadError.message : 'Не удалось загрузить контрагентов');
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [open, debouncedSearch, session]);

  const handleToggle = (row: ContractorListItem, unitId: number, checked: boolean) => {
    setDraftsById((prev) => ({
      ...prev,
      [row.userId]: { ...(prev[row.userId] ?? {}), [unitId]: checked },
    }));
  };

  const rowHasChanges = (row: ContractorListItem) => {
    const draft = draftsById[row.userId] ?? {};
    return (row.rootUnits?.items ?? []).some(
      (item) => item.canManage && Boolean(draft[item.unitId]) !== item.isBound,
    );
  };

  const rowCanManage = (row: ContractorListItem) =>
    Boolean(row.rootUnits?.canManage) && (row.rootUnits?.items ?? []).some((item) => item.canManage);

  const persistRow = async (row: ContractorListItem) => {
    const draft = draftsById[row.userId] ?? {};
    const manageableBoundIds = (row.rootUnits?.items ?? [])
      .filter((item) => item.canManage && Boolean(draft[item.unitId]))
      .map((item) => item.unitId);

    const updated = await updateContractorRootUnits(row.userId, manageableBoundIds);
    setRows((prev) => prev.map((item) => (item.userId === row.userId ? { ...item, rootUnits: updated } : item)));
    setDraftsById((prev) => ({
      ...prev,
      [row.userId]: Object.fromEntries(updated.items.map((item) => [item.unitId, item.isBound])),
    }));
  };

  const handleSaveRow = async (row: ContractorListItem) => {
    try {
      setSavingId(row.userId);
      await persistRow(row);
      showSystemToast({ severity: 'success', message: 'Привязки к подразделениям сохранены.' });
      await onSaved();
    } catch (saveError) {
      showErrorToast(saveError instanceof Error ? saveError.message : 'Не удалось сохранить привязки');
    } finally {
      setSavingId(null);
    }
  };

  const changedRows = rows.filter(rowHasChanges);

  const handleSaveAll = async () => {
    if (changedRows.length === 0) {
      return;
    }

    try {
      setIsSavingAll(true);
      let savedCount = 0;
      for (const row of changedRows) {
        await persistRow(row);
        savedCount += 1;
      }
      showSystemToast({
        severity: 'success',
        message: `Сохранены привязки для контрагентов: ${savedCount}.`,
      });
      await onSaved();
    } catch (saveError) {
      showErrorToast(saveError instanceof Error ? saveError.message : 'Не удалось сохранить привязки');
    } finally {
      setIsSavingAll(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ pr: 6 }}>
        <Stack spacing={0.25}>
          <Typography component="span" sx={{ fontSize: 18, fontWeight: 700 }}>
            Контрагенты и подразделения
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {departmentName
              ? `Отметьте подразделения, к которым привязан контрагент (контекст: «${departmentName}»).`
              : 'Отметьте подразделения, к которым привязан контрагент.'}
          </Typography>
        </Stack>
        <Tooltip title="Закрыть">
          <IconButton onClick={onClose} aria-label="Закрыть" sx={{ position: 'absolute', top: 8, right: 8 }}>
            <CloseRoundedIcon />
          </IconButton>
        </Tooltip>
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={1.5}>
          <TextField
            fullWidth
            size="small"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Поиск по логину, ФИО, компании, e-mail"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchRoundedIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          {isLoading ? (
            <Box sx={{ display: 'grid', placeItems: 'center', minHeight: 160 }}>
              <CircularProgress />
            </Box>
          ) : rows.length === 0 ? (
            <Box sx={{ py: 3, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Контрагенты не найдены.
              </Typography>
            </Box>
          ) : (
            <TableContainer sx={{ maxHeight: '60vh' }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700, minWidth: 220 }}>Контрагент</TableCell>
                    <TableCell sx={{ fontWeight: 700, minWidth: 260 }}>Подразделения</TableCell>
                    <TableCell sx={{ fontWeight: 700, width: 130 }} align="right">
                      Действия
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((row) => {
                    const { login, fullName, company } = buildContractorLabel(row);
                    const items = row.rootUnits?.items ?? [];
                    const draft = draftsById[row.userId] ?? {};
                    const canManage = rowCanManage(row);
                    const hasChanges = rowHasChanges(row);
                    const isRowSaving = savingId === row.userId || isSavingAll;

                    return (
                      <TableRow key={row.userId} hover sx={{ verticalAlign: 'top' }}>
                        <TableCell sx={{ minWidth: 220 }}>
                          <Stack spacing={0.1}>
                            <Typography sx={{ fontSize: 13.5, fontWeight: 700, overflowWrap: 'anywhere' }}>
                              {login}
                            </Typography>
                            <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>
                              {fullName ?? '—'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
                              {company ?? 'Компания не указана'}
                            </Typography>
                          </Stack>
                        </TableCell>
                        <TableCell sx={{ minWidth: 260 }}>
                          {items.length === 0 ? (
                            <Typography variant="body2" color="text.secondary">
                              Нет доступных подразделений.
                            </Typography>
                          ) : (
                            <FormGroup
                              sx={{
                                display: 'grid',
                                gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' },
                                columnGap: 1,
                              }}
                            >
                              {items.map((item) => (
                                <FormControlLabel
                                  key={`${row.userId}-${item.unitId}`}
                                  sx={{ m: 0 }}
                                  control={(
                                    <Checkbox
                                      size="small"
                                      checked={Boolean(draft[item.unitId])}
                                      disabled={!item.canManage || isRowSaving}
                                      onChange={(event) => handleToggle(row, item.unitId, event.target.checked)}
                                    />
                                  )}
                                  label={(
                                    <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>
                                      {item.unitName}
                                    </Typography>
                                  )}
                                />
                              ))}
                            </FormGroup>
                          )}
                        </TableCell>
                        <TableCell align="right" sx={{ width: 130 }}>
                          {canManage ? (
                            <Button
                              size="small"
                              variant="contained"
                              disabled={!hasChanges || isRowSaving}
                              onClick={() => void handleSaveRow(row)}
                              sx={{ textTransform: 'none', boxShadow: 'none', whiteSpace: 'nowrap' }}
                            >
                              {isRowSaving ? 'Сохранение...' : 'Сохранить'}
                            </Button>
                          ) : (
                            <Tooltip title="Нет прав на изменение привязок">
                              <Box
                                component="span"
                                sx={{
                                  fontSize: 12,
                                  color: alpha(hierarchyPageColors.textSecondary, 0.9),
                                }}
                              >
                                Только просмотр
                              </Box>
                            </Tooltip>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 1.5 }}>
        <Typography variant="caption" color="text.secondary" sx={{ mr: 'auto' }}>
          {changedRows.length > 0 ? `Несохранённых изменений: ${changedRows.length}` : 'Нет несохранённых изменений'}
        </Typography>
        <Button onClick={onClose} disabled={isSavingAll || savingId !== null} sx={{ textTransform: 'none' }}>
          Закрыть
        </Button>
        <Button
          variant="contained"
          disabled={changedRows.length === 0 || isSavingAll || savingId !== null}
          onClick={() => void handleSaveAll()}
          sx={{ textTransform: 'none', boxShadow: 'none' }}
        >
          {isSavingAll ? 'Сохранение...' : 'Сохранить всё'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
