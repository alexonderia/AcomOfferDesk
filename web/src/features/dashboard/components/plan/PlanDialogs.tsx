import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import type { UseFormReturn } from 'react-hook-form';
import type { PlanDelegateCandidate, PlanTreeNode } from '@shared/api/plans';
import type {
  DelegateFormValues,
  EditFormValues,
  RootPlanFormValues,
  SubplanFormValues,
} from './planDashboardForms';
import { textFieldAutocompleteProps } from '@shared/lib/forms';
import { RequiredFieldLabel } from '@shared/components/forms/RequiredFieldLabel';
import { rootPlanSchema, subplanSchema, delegateSchema } from './planDashboardForms';
import type { SafeParseReturnType } from 'zod';

const requiredLabel = (label: string, field: string, validation: SafeParseReturnType<unknown, unknown>) => (
  <RequiredFieldLabel label={label} isValid={validation.success || !validation.error.issues.some((issue) => issue.path.length === 0 || issue.path[0] === field)} />
);

type PlanDialogsProps = {
  isMutating: boolean;
  canCreateRootPlan: boolean;
  rootDialogOpen: boolean;
  subplanNode: PlanTreeNode | null;
  delegateNode: PlanTreeNode | null;
  delegateCandidates: PlanDelegateCandidate[];
  isCandidatesLoading: boolean;
  editNode: PlanTreeNode | null;
  deleteNode: PlanTreeNode | null;
  closeNode: PlanTreeNode | null;
  rootPlanForm: UseFormReturn<RootPlanFormValues>;
  subplanForm: UseFormReturn<SubplanFormValues>;
  delegateForm: UseFormReturn<DelegateFormValues>;
  editForm: UseFormReturn<EditFormValues>;
  onCloseRootDialog: () => void;
  onCloseSubplanDialog: () => void;
  onCloseDelegateDialog: () => void;
  onCloseEditDialog: () => void;
  onCloseDeleteDialog: () => void;
  onCloseCloseDialog: () => void;
  onSubmitRoot: () => void;
  onSubmitSubplan: () => void;
  onSubmitDelegate: () => void;
  onSubmitEdit: () => void;
  onConfirmDelete: () => void;
  onConfirmClose: () => void;
};

export const PlanDialogs = ({
  isMutating,
  canCreateRootPlan,
  rootDialogOpen,
  subplanNode,
  delegateNode,
  delegateCandidates,
  isCandidatesLoading,
  editNode,
  deleteNode,
  closeNode,
  rootPlanForm,
  subplanForm,
  delegateForm,
  editForm,
  onCloseRootDialog,
  onCloseSubplanDialog,
  onCloseDelegateDialog,
  onCloseEditDialog,
  onCloseDeleteDialog,
  onCloseCloseDialog,
  onSubmitRoot,
  onSubmitSubplan,
  onSubmitDelegate,
  onSubmitEdit,
  onConfirmDelete,
  onConfirmClose,
}: PlanDialogsProps) => {
  const rootValidation = rootPlanSchema.safeParse(rootPlanForm.watch());
  const subplanValidation = subplanSchema.safeParse(subplanForm.watch());
  const delegateValidation = delegateSchema.safeParse(delegateForm.watch());
  return (
    <>
      <Dialog open={rootDialogOpen} onClose={onCloseRootDialog} fullWidth maxWidth="sm">
        <DialogTitle>Создать план</DialogTitle>
        <DialogContent>
          <Stack spacing={1.2} sx={{ mt: 0.5 }}>
            <TextField
              label={requiredLabel('Название плана', 'name', rootValidation)}
              required
              InputLabelProps={{ required: false }}
              size="small"
              error={Boolean(rootPlanForm.formState.errors.name)}
              helperText={rootPlanForm.formState.errors.name?.message}
              {...textFieldAutocompleteProps('name')}
              {...rootPlanForm.register('name')}
            />
            <TextField
              type="date"
              label={requiredLabel('Дата начала', 'periodStart', rootValidation)}
              required
              size="small"
              InputLabelProps={{ shrink: true, required: false }}
              error={Boolean(rootPlanForm.formState.errors.periodStart)}
              helperText={rootPlanForm.formState.errors.periodStart?.message}
              {...textFieldAutocompleteProps('periodStart')}
              {...rootPlanForm.register('periodStart')}
            />
            <TextField
              type="date"
              label={requiredLabel('Дата окончания', 'periodEnd', rootValidation)}
              required
              size="small"
              InputLabelProps={{ shrink: true, required: false }}
              error={Boolean(rootPlanForm.formState.errors.periodEnd)}
              helperText={rootPlanForm.formState.errors.periodEnd?.message}
              {...textFieldAutocompleteProps('periodEnd')}
              {...rootPlanForm.register('periodEnd')}
            />
            <TextField
              label={requiredLabel('Сумма плана', 'planAmount', rootValidation)}
              required
              InputLabelProps={{ required: false }}
              size="small"
              error={Boolean(rootPlanForm.formState.errors.planAmount)}
              helperText={rootPlanForm.formState.errors.planAmount?.message}
              {...textFieldAutocompleteProps('planAmount')}
              {...rootPlanForm.register('planAmount')}
            />
            <Alert severity="info">
              Рекомендуем декомпозировать глобальные планы на более мелкие, например помесячно.
            </Alert>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onCloseRootDialog}>Отмена</Button>
          <Button variant="contained" disabled={!canCreateRootPlan || isMutating} onClick={onSubmitRoot}>
            Создать
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(subplanNode)} onClose={onCloseSubplanDialog} fullWidth maxWidth="sm">
        <DialogTitle>Создать подплан</DialogTitle>
        <DialogContent>
          <Stack spacing={1.2} sx={{ mt: 0.5 }}>
            <Typography variant="body2" color="text.secondary">
              Родитель: {subplanNode?.plan_name}
            </Typography>
            <TextField
              label={requiredLabel('Название подплана', 'name', subplanValidation)}
              required
              InputLabelProps={{ required: false }}
              size="small"
              error={Boolean(subplanForm.formState.errors.name)}
              helperText={subplanForm.formState.errors.name?.message}
              {...textFieldAutocompleteProps('name')}
              {...subplanForm.register('name')}
            />
            <FormControl fullWidth size="small" error={Boolean(subplanForm.formState.errors.childUserId)}>
              <InputLabel id="subplan-child-user-label">{requiredLabel('Исполнитель', 'childUserId', subplanValidation)}</InputLabel>
              <Select
                labelId="subplan-child-user-label"
                label={requiredLabel('Исполнитель', 'childUserId', subplanValidation)}
                inputProps={{ 'aria-required': true }}
                value={subplanForm.watch('childUserId')}
                onChange={(event) => {
                  subplanForm.setValue('childUserId', event.target.value, { shouldValidate: true });
                }}
              >
                <MenuItem value={subplanNode?.user_id ?? ''}>
                  {subplanNode?.user_name ?? 'Текущий владелец плана'}
                </MenuItem>
                {delegateCandidates.map((candidate) => (
                  <MenuItem key={`subplan-${candidate.user_id}`} value={candidate.user_id}>
                    {candidate.full_name || candidate.user_id} ({candidate.role_name})
                  </MenuItem>
                ))}
              </Select>
              {subplanForm.formState.errors.childUserId ? (
                <Typography variant="caption" color="error">
                  {subplanForm.formState.errors.childUserId.message}
                </Typography>
              ) : null}
            </FormControl>
            <TextField
              type="date"
              label={requiredLabel('Дата начала подплана', 'periodStart', subplanValidation)}
              required
              size="small"
              InputLabelProps={{ shrink: true, required: false }}
              inputProps={{
                min: subplanNode?.period_start,
                max: subplanNode?.period_end,
                autoComplete: 'off',
              }}
              error={Boolean(subplanForm.formState.errors.periodStart)}
              helperText={subplanForm.formState.errors.periodStart?.message}
              {...subplanForm.register('periodStart')}
            />
            <TextField
              type="date"
              label={requiredLabel('Дата окончания подплана', 'periodEnd', subplanValidation)}
              required
              size="small"
              InputLabelProps={{ shrink: true, required: false }}
              inputProps={{
                min: subplanNode?.period_start,
                max: subplanNode?.period_end,
                autoComplete: 'off',
              }}
              error={Boolean(subplanForm.formState.errors.periodEnd)}
              helperText={subplanForm.formState.errors.periodEnd?.message}
              {...subplanForm.register('periodEnd')}
            />
            <TextField
              label={requiredLabel('Сумма подплана', 'amount', subplanValidation)}
              required
              InputLabelProps={{ required: false }}
              size="small"
              error={Boolean(subplanForm.formState.errors.amount)}
              helperText={subplanForm.formState.errors.amount?.message}
              {...textFieldAutocompleteProps('amount')}
              {...subplanForm.register('amount')}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onCloseSubplanDialog}>Отмена</Button>
          <Button variant="contained" disabled={isMutating} onClick={onSubmitSubplan}>
            Создать
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(delegateNode)} onClose={onCloseDelegateDialog} fullWidth maxWidth="sm">
        <DialogTitle>Делегировать план</DialogTitle>
        <DialogContent>
          <Stack spacing={1.2} sx={{ mt: 0.5 }}>
            {isCandidatesLoading ? <Alert severity="info">Загрузка подчиненных...</Alert> : null}
            <Typography variant="body2" color="text.secondary">
              План: {delegateNode?.plan_name}
            </Typography>
            <FormControl fullWidth size="small" error={Boolean(delegateForm.formState.errors.childUserId)}>
              <InputLabel id="delegate-child-user-label">{requiredLabel('Подчиненный', 'childUserId', delegateValidation)}</InputLabel>
              <Select
                labelId="delegate-child-user-label"
                label={requiredLabel('Подчиненный', 'childUserId', delegateValidation)}
                inputProps={{ 'aria-required': true }}
                value={delegateForm.watch('childUserId')}
                onChange={(event) => {
                  delegateForm.setValue('childUserId', event.target.value, { shouldValidate: true });
                }}
              >
                {delegateCandidates.map((candidate) => (
                  <MenuItem key={candidate.user_id} value={candidate.user_id}>
                    {candidate.full_name || candidate.user_id} ({candidate.role_name})
                  </MenuItem>
                ))}
              </Select>
              {delegateForm.formState.errors.childUserId ? (
                <Typography variant="caption" color="error">
                  {delegateForm.formState.errors.childUserId.message}
                </Typography>
              ) : null}
            </FormControl>
            <TextField
              type="date"
              label={requiredLabel('Дата начала делегирования', 'childPeriodStart', delegateValidation)}
              required
              size="small"
              InputLabelProps={{ shrink: true, required: false }}
              inputProps={{
                min: delegateNode?.period_start,
                max: delegateNode?.period_end,
                autoComplete: 'off',
              }}
              error={Boolean(delegateForm.formState.errors.childPeriodStart)}
              helperText={delegateForm.formState.errors.childPeriodStart?.message}
              {...delegateForm.register('childPeriodStart')}
            />
            <TextField
              label={requiredLabel('Сумма делегирования', 'childPlanAmount', delegateValidation)}
              required
              InputLabelProps={{ required: false }}
              size="small"
              error={Boolean(delegateForm.formState.errors.childPlanAmount)}
              helperText={delegateForm.formState.errors.childPlanAmount?.message}
              {...textFieldAutocompleteProps('childPlanAmount')}
              {...delegateForm.register('childPlanAmount')}
            />
            {!isCandidatesLoading && delegateCandidates.length === 0 ? (
              <Alert severity="info">Нет доступных прямых подчиненных для делегирования.</Alert>
            ) : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onCloseDelegateDialog}>Отмена</Button>
          <Button variant="contained" disabled={isMutating || isCandidatesLoading} onClick={onSubmitDelegate}>
            Делегировать
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(editNode)} onClose={onCloseEditDialog} fullWidth maxWidth="xs">
        <DialogTitle>Редактирование плана</DialogTitle>
        <DialogContent>
          <Stack spacing={1.2} sx={{ mt: 0.5 }}>
            <Typography variant="body2" color="text.secondary">
              {editNode?.user_name}
            </Typography>
            <TextField
              label="Название плана"
              size="small"
              error={Boolean(editForm.formState.errors.name)}
              helperText={editForm.formState.errors.name?.message}
              {...textFieldAutocompleteProps('name')}
              {...editForm.register('name')}
            />
            <TextField
              label="Новая сумма"
              size="small"
              error={Boolean(editForm.formState.errors.planAmount)}
              helperText={editForm.formState.errors.planAmount?.message}
              {...textFieldAutocompleteProps('planAmount')}
              {...editForm.register('planAmount')}
            />
            <TextField
              type="date"
              label="Дата окончания"
              size="small"
              InputLabelProps={{ shrink: true }}
              error={Boolean(editForm.formState.errors.periodEnd)}
              helperText={editForm.formState.errors.periodEnd?.message}
              {...textFieldAutocompleteProps('periodEnd')}
              {...editForm.register('periodEnd')}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onCloseEditDialog}>Отмена</Button>
          <Button variant="contained" disabled={isMutating} onClick={onSubmitEdit}>
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(deleteNode)} onClose={onCloseDeleteDialog} fullWidth maxWidth="xs">
        <DialogTitle>Удаление плана</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            Удалить план {deleteNode?.plan_name}? Это действие необратимо.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={onCloseDeleteDialog}>Отмена</Button>
          <Button color="error" variant="contained" disabled={isMutating} onClick={onConfirmDelete}>
            Удалить
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(closeNode)} onClose={onCloseCloseDialog} fullWidth maxWidth="xs">
        <DialogTitle>Закрытие плана</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            Закрыть план {closeNode?.plan_name}? После закрытия редактирование и делегирование будут недоступны.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={onCloseCloseDialog}>Отмена</Button>
          <Button color="warning" variant="contained" disabled={isMutating} onClick={onConfirmClose}>
            Закрыть
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};
