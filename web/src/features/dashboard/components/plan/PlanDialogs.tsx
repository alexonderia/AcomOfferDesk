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
  return (
    <>
      <Dialog open={rootDialogOpen} onClose={onCloseRootDialog} fullWidth maxWidth="sm">
        <DialogTitle>Создать план</DialogTitle>
        <DialogContent>
          <Stack spacing={1.2} sx={{ mt: 0.5 }}>
            <TextField
              label="Название плана"
              size="small"
              error={Boolean(rootPlanForm.formState.errors.name)}
              helperText={rootPlanForm.formState.errors.name?.message}
              {...rootPlanForm.register('name')}
            />
            <TextField
              type="date"
              label="Дата начала"
              size="small"
              InputLabelProps={{ shrink: true }}
              error={Boolean(rootPlanForm.formState.errors.periodStart)}
              helperText={rootPlanForm.formState.errors.periodStart?.message}
              {...rootPlanForm.register('periodStart')}
            />
            <TextField
              type="date"
              label="Дата окончания"
              size="small"
              InputLabelProps={{ shrink: true }}
              error={Boolean(rootPlanForm.formState.errors.periodEnd)}
              helperText={rootPlanForm.formState.errors.periodEnd?.message}
              {...rootPlanForm.register('periodEnd')}
            />
            <TextField
              label="Сумма плана"
              size="small"
              error={Boolean(rootPlanForm.formState.errors.planAmount)}
              helperText={rootPlanForm.formState.errors.planAmount?.message}
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
              label="Название подплана"
              size="small"
              error={Boolean(subplanForm.formState.errors.name)}
              helperText={subplanForm.formState.errors.name?.message}
              {...subplanForm.register('name')}
            />
            <FormControl fullWidth size="small" error={Boolean(subplanForm.formState.errors.childUserId)}>
              <InputLabel id="subplan-child-user-label">Исполнитель</InputLabel>
              <Select
                labelId="subplan-child-user-label"
                label="Исполнитель"
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
              label="Дата начала подплана"
              size="small"
              InputLabelProps={{ shrink: true }}
              inputProps={{ min: subplanNode?.period_start, max: subplanNode?.period_end }}
              error={Boolean(subplanForm.formState.errors.periodStart)}
              helperText={subplanForm.formState.errors.periodStart?.message}
              {...subplanForm.register('periodStart')}
            />
            <TextField
              type="date"
              label="Дата окончания подплана"
              size="small"
              InputLabelProps={{ shrink: true }}
              inputProps={{ min: subplanNode?.period_start, max: subplanNode?.period_end }}
              error={Boolean(subplanForm.formState.errors.periodEnd)}
              helperText={subplanForm.formState.errors.periodEnd?.message}
              {...subplanForm.register('periodEnd')}
            />
            <TextField
              label="Сумма подплана"
              size="small"
              error={Boolean(subplanForm.formState.errors.amount)}
              helperText={subplanForm.formState.errors.amount?.message}
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
              <InputLabel id="delegate-child-user-label">Подчиненный</InputLabel>
              <Select
                labelId="delegate-child-user-label"
                label="Подчиненный"
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
              label="Дата начала делегирования"
              size="small"
              InputLabelProps={{ shrink: true }}
              inputProps={{ min: delegateNode?.period_start, max: delegateNode?.period_end }}
              error={Boolean(delegateForm.formState.errors.childPeriodStart)}
              helperText={delegateForm.formState.errors.childPeriodStart?.message}
              {...delegateForm.register('childPeriodStart')}
            />
            <TextField
              label="Сумма делегирования"
              size="small"
              error={Boolean(delegateForm.formState.errors.childPlanAmount)}
              helperText={delegateForm.formState.errors.childPlanAmount?.message}
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
              {...editForm.register('name')}
            />
            <TextField
              label="Новая сумма"
              size="small"
              error={Boolean(editForm.formState.errors.planAmount)}
              helperText={editForm.formState.errors.planAmount?.message}
              {...editForm.register('planAmount')}
            />
            <TextField
              type="date"
              label="Дата окончания"
              size="small"
              InputLabelProps={{ shrink: true }}
              error={Boolean(editForm.formState.errors.periodEnd)}
              helperText={editForm.formState.errors.periodEnd?.message}
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
