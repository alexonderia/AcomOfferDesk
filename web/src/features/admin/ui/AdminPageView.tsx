import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogContent,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
  type SelectChangeEvent
} from '@mui/material';
import { alpha, type Theme } from '@mui/material/styles';
import { UsersTable } from '@features/admin/components/UsersTable';
import { ROLE } from '@shared/constants/roles';
import { ValidatedTextField } from '@shared/components/forms/ValidatedTextField';
import { formatRuPhone } from '@shared/lib/phone';
import type { UserTab } from '../model/constants';
import { useAdminPage, type AdminUserFormValues } from '../model/useAdminPage';

const dialogPaperSx = (theme: Theme) => ({
  borderRadius: 2,
  px: { xs: 2.5, sm: 3.5 },
  py: { xs: 3, sm: 3.5 },
  backgroundColor: theme.palette.background.default,
  maxHeight: 'min(760px, calc(100vh - 32px))',
  overflow: 'hidden',
  boxShadow: `0 24px 80px ${alpha(theme.palette.common.black, 0.18)}`
});

const dialogContentSx = {
  p: 0,
  overflowX: 'hidden',
  overflowY: 'auto',
  scrollbarWidth: 'none',
  '&::-webkit-scrollbar': {
    display: 'none'
  }
};

const inputFieldSx = {
  '& .MuiOutlinedInput-root': {
    borderRadius: 1,
    backgroundColor: 'background.paper'
  }
};

const roleNameById: Record<number, string> = {
  [ROLE.PROJECT_MANAGER]: 'РП',
  [ROLE.LEAD_ECONOMIST]: 'ВЭ',
  [ROLE.ECONOMIST]: 'Экономист',
};

export const AdminPageView = () => {
  const {
    isLeadLike,
    isAdmin,
    canViewRoleIds,
    isDialogOpen,
    setIsDialogOpen,
    activeTab,
    handleTabChange,
    users,
    isLoadingUsers,
    usersError,
    canUpdateStatus,
    canUpdateRole,
    roleUpdateOptions,
    roleOptions,
    userTabs,
    getRoleLabel,
    canOpenCreateDialog,
    isContractorRole,
    requiresParent,
    managerOptions,
    loadUsers,
    handleClose,
    onSubmit,
    form
  } = useAdminPage();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting, touchedFields, submitCount }
  } = form;

  const selectedRoleId = watch('role_id');

  const handleRoleSelectChange = (event: SelectChangeEvent<UserTab>) => {
    handleTabChange(event.target.value as UserTab);
  };

  const companyPhoneRegistration = register('company_phone');
  const touchedMap = touchedFields as Partial<Record<keyof AdminUserFormValues, unknown>>;
  const getFieldError = (field: keyof AdminUserFormValues) => {
    const shouldShow = submitCount > 0 || Boolean(touchedMap[field]);
    const message = errors[field]?.message;
    if (!shouldShow || typeof message !== 'string') {
      return undefined;
    }
    return message;
  };

  return (
    <Stack spacing={2}>
      {!isLeadLike && !isAdmin ? (
        <Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5} alignItems={{ sm: 'center' }} flexWrap="wrap" sx={{ width: '100%' }}>
          <Select
            size="small"
            value={activeTab}
            onChange={handleRoleSelectChange}
            sx={{ minWidth: { xs: '100%', sm: 300 }, flexShrink: 0 }}
          >
            {userTabs.map((tab) => (
              <MenuItem key={tab.value} value={tab.value}>{tab.label}</MenuItem>
            ))}
          </Select>
        </Stack>
      ) : null}

      {usersError ? <Alert severity="error">{usersError}</Alert> : null}

      <UsersTable
        users={users}
        isLoading={isLoadingUsers}
        emptyMessage="Список пользователей пока пуст."
        getRoleLabel={getRoleLabel}
        isContractorsTab={activeTab === 'contractors'}
        canViewRoleIds={canViewRoleIds}
        canUpdateStatus={canUpdateStatus}
        canUpdateRole={canUpdateRole}
        allowedRoleOptions={roleUpdateOptions}
        onStatusUpdated={loadUsers}
        onAddClick={canOpenCreateDialog ? () => setIsDialogOpen(true) : undefined}
      />

      <Dialog
        open={isDialogOpen}
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: dialogPaperSx }}
      >
        <DialogContent sx={dialogContentSx}>
          <Box component="form" onSubmit={handleSubmit(onSubmit)}>
            <Stack spacing={2}>
              <Typography variant="h5" fontWeight={600} lineHeight={1}>
                {isContractorRole ? 'Создание контрагента' : 'Создание нового пользователя'}
              </Typography>
              <TextField
                label="Роль пользователя"
                select
                error={Boolean(getFieldError('role_id'))}
                helperText={getFieldError('role_id')}
                defaultValue={roleOptions[0]?.id ?? ROLE.ADMIN}
                {...register('role_id', { valueAsNumber: true })}
                sx={inputFieldSx}
              >
                {roleOptions.map((option) => (
                  <MenuItem key={option.id} value={option.id}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>

              {isContractorRole ? (
                <>
                  <ValidatedTextField
                    label="Наименование компании"
                    fieldName="company_name"
                    error={Boolean(getFieldError('company_name'))}
                    helperText={getFieldError('company_name')}
                    registration={register('company_name')}
                    sx={inputFieldSx}
                  />
                  <ValidatedTextField
                    label="ИНН"
                    fieldName="inn"
                    error={Boolean(getFieldError('inn'))}
                    helperText={getFieldError('inn')}
                    registration={register('inn')}
                    sx={inputFieldSx}
                  />
                  <ValidatedTextField
                    label="Телефон компании"
                    fieldName="company_phone"
                    placeholder="+7 (900) 999-88-77"
                    error={Boolean(getFieldError('company_phone'))}
                    helperText={getFieldError('company_phone')}
                    name={companyPhoneRegistration.name}
                    inputRef={companyPhoneRegistration.ref}
                    onBlur={companyPhoneRegistration.onBlur}
                    onChange={(event) => {
                      const formatted = formatRuPhone(event.target.value);
                      setValue('company_phone', formatted, {
                        shouldDirty: true,
                        shouldTouch: true,
                        shouldValidate: true
                      });
                    }}
                    sx={inputFieldSx}
                  />
                  <ValidatedTextField
                    label="E-mail компании"
                    fieldName="company_mail"
                    error={Boolean(getFieldError('company_mail'))}
                    helperText={getFieldError('company_mail')}
                    registration={register('company_mail')}
                    sx={inputFieldSx}
                  />
                  <ValidatedTextField
                    label="Адрес"
                    fieldName="address"
                    error={Boolean(getFieldError('address'))}
                    helperText={getFieldError('address')}
                    registration={register('address')}
                    sx={inputFieldSx}
                  />
                  <ValidatedTextField
                    label="Дополнительная информация"
                    fieldName="note"
                    multiline
                    minRows={2}
                    error={Boolean(getFieldError('note'))}
                    helperText={getFieldError('note')}
                    registration={register('note')}
                    sx={inputFieldSx}
                  />
                </>
              ) : (
                <>
                  <ValidatedTextField
                    label="Логин"
                    fieldName="login"
                    error={Boolean(getFieldError('login'))}
                    helperText={getFieldError('login')}
                    registration={register('login')}
                    sx={inputFieldSx}
                  />
                  <ValidatedTextField
                    label="Пароль"
                    type="password"
                    fieldName="password"
                    error={Boolean(getFieldError('password'))}
                    helperText={getFieldError('password')}
                    registration={register('password')}
                    sx={{ display: 'none' }}
                  />
                  <ValidatedTextField
                    label="Повторите пароль"
                    type="password"
                    fieldName="confirmPassword"
                    error={Boolean(getFieldError('confirmPassword'))}
                    helperText={getFieldError('confirmPassword')}
                    registration={register('confirmPassword')}
                    sx={{ display: 'none' }}
                  />
                  <ValidatedTextField
                    label="E-mail"
                    fieldName="mail"
                    error={Boolean(getFieldError('mail'))}
                    helperText={getFieldError('mail')}
                    registration={register('mail')}
                    sx={inputFieldSx}
                  />

                  {selectedRoleId === ROLE.PROJECT_MANAGER || requiresParent ? (
                    <TextField
                      label={
                        selectedRoleId === ROLE.ECONOMIST
                          ? 'Руководитель (ведущий экономист или экономист)'
                          : selectedRoleId === ROLE.LEAD_ECONOMIST
                            ? 'Руководитель (руководитель проекта или ведущий экономист)'
                            : 'Руководитель (руководитель проекта)'
                      }
                      select
                      error={Boolean(getFieldError('id_parent'))}
                      helperText={getFieldError('id_parent') ?? (managerOptions.length ? '' : 'Нет доступных руководителей')}
                      {...register('id_parent')}
                      sx={inputFieldSx}
                    >
                      {!requiresParent ? (
                        <MenuItem value="">
                          Без руководителя
                        </MenuItem>
                      ) : null}
                      {managerOptions.map((manager) => (
                        <MenuItem key={manager.user_id} value={manager.user_id}>
                          {manager.full_name
                            ? `${roleNameById[manager.role_id] ?? `Роль ${manager.role_id}`} — ${manager.full_name} (${manager.user_id})`
                            : `${roleNameById[manager.role_id] ?? `Роль ${manager.role_id}`} — ${manager.user_id}`}
                        </MenuItem>
                      ))}
                    </TextField>
                  ) : null}
                </>
              )}

              <Button
                type="submit"
                variant="contained"
                fullWidth
                disabled={isSubmitting}
                sx={{ borderRadius: 1, textTransform: 'none', py: 1.25, fontSize: 16, fontWeight: 700, boxShadow: 'none' }}
              >
                {isSubmitting
                  ? 'Сохранение...'
                  : isContractorRole
                    ? 'Создать контрагента'
                    : 'Создать пользователя'}
              </Button>
            </Stack>
          </Box>
        </DialogContent>
      </Dialog>
    </Stack>
  );
};
