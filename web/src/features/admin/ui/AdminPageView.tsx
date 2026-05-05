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

export const AdminPageView = () => {
  const {
    isLeadLike,
    isAdmin,
    canViewRoleIds,
    isDialogOpen,
    setIsDialogOpen,
    errorMessage,
    successMessage,
    activeTab,
    handleTabChange,
    users,
    isLoadingUsers,
    usersError,
    canUpdateStatus,
    canUpdateRole,
    roleOptions,
    userTabs,
    getRoleLabel,
    canCreateUser,
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
        allowedRoleOptions={[ROLE.ADMIN, ROLE.ECONOMIST]}
        onStatusUpdated={loadUsers}
        onAddClick={canCreateUser ? () => setIsDialogOpen(true) : undefined}
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
                  <TextField
                    label="Наименование компании"
                    error={Boolean(getFieldError('company_name'))}
                    helperText={getFieldError('company_name')}
                    {...register('company_name')}
                    sx={inputFieldSx}
                  />
                  <TextField
                    label="ИНН"
                    error={Boolean(getFieldError('inn'))}
                    helperText={getFieldError('inn')}
                    {...register('inn')}
                    sx={inputFieldSx}
                  />
                  <TextField
                    label="Телефон компании"
                    placeholder="+7 (900) 999-88-77"
                    error={Boolean(getFieldError('company_phone'))}
                    helperText={getFieldError('company_phone')}
                    {...companyPhoneRegistration}
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
                  <TextField
                    label="E-mail компании"
                    error={Boolean(getFieldError('company_mail'))}
                    helperText={getFieldError('company_mail')}
                    {...register('company_mail')}
                    sx={inputFieldSx}
                  />
                  <TextField
                    label="Адрес"
                    error={Boolean(getFieldError('address'))}
                    helperText={getFieldError('address')}
                    {...register('address')}
                    sx={inputFieldSx}
                  />
                  <TextField
                    label="Дополнительная информация"
                    multiline
                    minRows={2}
                    error={Boolean(getFieldError('note'))}
                    helperText={getFieldError('note')}
                    {...register('note')}
                    sx={inputFieldSx}
                  />
                </>
              ) : (
                <>
                  <TextField
                    label="Логин"
                    error={Boolean(getFieldError('login'))}
                    helperText={getFieldError('login')}
                    {...register('login')}
                    sx={inputFieldSx}
                  />
                  <TextField
                    label="Пароль"
                    type="password"
                    error={Boolean(getFieldError('password'))}
                    helperText={getFieldError('password')}
                    {...register('password')}
                    sx={{ display: 'none' }}
                  />
                  <TextField
                    label="Повторите пароль"
                    type="password"
                    error={Boolean(getFieldError('confirmPassword'))}
                    helperText={getFieldError('confirmPassword')}
                    {...register('confirmPassword')}
                    sx={{ display: 'none' }}
                  />
                  <TextField
                    label="E-mail"
                    error={Boolean(getFieldError('mail'))}
                    helperText={getFieldError('mail')}
                    {...register('mail')}
                    sx={inputFieldSx}
                  />

                  {requiresParent ? (
                    <TextField
                      label={selectedRoleId === ROLE.ECONOMIST ? 'Руководитель (экономист или ведущий экономист)' : 'Руководитель (руководитель проекта)'}
                      select
                      error={Boolean(getFieldError('id_parent'))}
                      helperText={getFieldError('id_parent') ?? (managerOptions.length ? '' : 'Нет доступных руководителей')}
                      {...register('id_parent')}
                      sx={inputFieldSx}
                    >
                      {managerOptions.map((manager) => (
                        <MenuItem key={manager.user_id} value={manager.user_id}>
                          {manager.full_name ? `${manager.full_name} (${manager.user_id})` : manager.user_id}
                        </MenuItem>
                      ))}
                    </TextField>
                  ) : null}
                </>
              )}

              {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}
              {successMessage ? <Alert severity="success">{successMessage}</Alert> : null}

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
