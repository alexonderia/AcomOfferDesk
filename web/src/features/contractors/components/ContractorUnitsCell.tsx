import AccountTreeOutlined from '@mui/icons-material/AccountTreeOutlined';
import {
  Alert,
  Button,
  Checkbox,
  CircularProgress,
  FormControlLabel,
  FormGroup,
  Popover,
  Stack,
  Typography,
} from '@mui/material';
import { useMemo, useState, type MouseEvent } from 'react';
import type { ContractorListItem } from '@shared/api/contractors/listContractors';
import {
  getContractorRootUnits,
  type ContractorRootUnitsResult,
} from '@shared/api/contractors/getContractorRootUnits';
import { updateContractorRootUnits } from '@shared/api/contractors/updateContractorRootUnits';
import { useSystemToasts } from '@shared/ui/toasts';

export type ContractorUnitsCellProps = {
  contractor: ContractorListItem;
  onSaved: () => Promise<void> | void;
};

export const ContractorUnitsCell = ({ contractor, onSaved }: ContractorUnitsCellProps) => {
  const { showSystemToast } = useSystemToasts();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ContractorRootUnitsResult | null>(contractor.rootUnits);
  const [draftById, setDraftById] = useState<Record<number, boolean>>(() =>
    Object.fromEntries((contractor.rootUnits?.items ?? []).map((item) => [item.unitId, item.isBound])),
  );

  const canOpen =
    contractor.actions.manage_contractor_unit_bindings || contractor.actions.view_profile;

  const loadBindings = () => {
    setIsLoading(true);
    setError(null);
    void getContractorRootUnits(contractor.userId)
      .then((data) => {
        setResult(data);
        setDraftById(Object.fromEntries(data.items.map((item) => [item.unitId, item.isBound])));
      })
      .catch((err) => {
        setError(
          err instanceof Error ? err.message : 'Не удалось загрузить привязки к подразделениям',
        );
      })
      .finally(() => setIsLoading(false));
  };

  const handleOpen = (event: MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    // Bindings are preloaded with the list; fetch only if missing.
    if (!result) {
      loadBindings();
    }
  };

  const handleClose = () => {
    setAnchorEl(null);
    setError(null);
  };

  const manageableUnitIds = useMemo(
    () => result?.items.filter((item) => item.canManage).map((item) => item.unitId) ?? [],
    [result],
  );

  const hasChanges = useMemo(
    () =>
      result?.items.some((item) => item.canManage && draftById[item.unitId] !== item.isBound) ??
      false,
    [draftById, result],
  );

  const boundCount = useMemo(
    () => (result ? result.items.filter((item) => item.isBound).length : null),
    [result],
  );

  const handleToggle = (unitId: number, checked: boolean) => {
    setDraftById((prev) => ({ ...prev, [unitId]: checked }));
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setError(null);
      const updated = await updateContractorRootUnits(
        contractor.userId,
        manageableUnitIds.filter((unitId) => Boolean(draftById[unitId])),
      );
      setResult(updated);
      setDraftById(Object.fromEntries(updated.items.map((item) => [item.unitId, item.isBound])));
      showSystemToast({ severity: 'success', message: 'Привязки к подразделениям сохранены.' });
      await onSaved();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Не удалось сохранить привязки к подразделениям',
      );
    } finally {
      setIsSaving(false);
    }
  };

  if (!canOpen) {
    return <Typography color="text.disabled">—</Typography>;
  }

  const triggerLabel =
    boundCount === null ? 'Подразделения' : boundCount === 0 ? 'Не привязан' : `Привязок: ${boundCount}`;
  const canManageBindings =
    contractor.actions.manage_contractor_unit_bindings && Boolean(result?.canManage);

  return (
    <>
      <Button
        size="small"
        variant="outlined"
        startIcon={<AccountTreeOutlined fontSize="small" />}
        onClick={handleOpen}
        aria-label={`root-units-${contractor.userId}`}
        sx={{ textTransform: 'none', borderRadius: 1, minHeight: 32, whiteSpace: 'nowrap' }}
      >
        {triggerLabel}
      </Button>
      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        slotProps={{ paper: { sx: { p: 1.5, minWidth: 260, maxWidth: 360, borderRadius: 2 } } }}
      >
        <Stack spacing={1.2} onClick={(event) => event.stopPropagation()}>
          <Typography variant="subtitle2" fontWeight={600}>
            Подразделения
          </Typography>
          {isLoading ? (
            <Stack direction="row" spacing={1} alignItems="center">
              <CircularProgress size={16} />
              <Typography color="text.secondary" variant="body2">
                Загрузка...
              </Typography>
            </Stack>
          ) : null}
          {!isLoading && error ? <Alert severity="error">{error}</Alert> : null}
          {!isLoading && !error && result ? (
            result.items.length > 0 ? (
              <FormGroup>
                {result.items.map((item) => (
                  <FormControlLabel
                    key={`${contractor.userId}-${item.unitId}`}
                    control={(
                      <Checkbox
                        size="small"
                        checked={Boolean(draftById[item.unitId])}
                        disabled={!item.canManage || isSaving}
                        onChange={(event) => handleToggle(item.unitId, event.target.checked)}
                      />
                    )}
                    label={item.unitName}
                  />
                ))}
              </FormGroup>
            ) : (
              <Typography color="text.secondary" variant="body2">
                Нет доступных подразделений.
              </Typography>
            )
          ) : null}
          {canManageBindings ? (
            <Stack direction="row" justifyContent="flex-end" spacing={1}>
              <Button size="small" onClick={handleClose} sx={{ textTransform: 'none' }}>
                Закрыть
              </Button>
              <Button
                size="small"
                variant="contained"
                onClick={() => void handleSave()}
                disabled={isSaving || !hasChanges}
                sx={{ textTransform: 'none', boxShadow: 'none' }}
              >
                {isSaving ? 'Сохранение...' : 'Сохранить'}
              </Button>
            </Stack>
          ) : null}
        </Stack>
      </Popover>
    </>
  );
};
