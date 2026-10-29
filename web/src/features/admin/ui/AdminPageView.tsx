import {
  Autocomplete,
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
import ForwardToInboxOutlined from '@mui/icons-material/ForwardToInboxOutlined';
import { useTheme } from '@mui/material/styles';
import { useMemo, useState } from 'react';
import { useSetPageBreadcrumbActions } from '@app/layouts/PageBreadcrumbActions';
import { useAuth } from '@app/providers/AuthProvider';
import { UsersTable } from '@features/admin/components/UsersTable';
import { ContractorInviteDialog } from '@features/contractors/components/ContractorInviteDialog';
import { ContractorsListView } from '@features/contractors/components/ContractorsListView';
import { ManualContractorDuplicatePanel } from '@features/contractors/components/ManualContractorDuplicatePanel';
import { ROLE } from '@shared/constants/roles';
import { hasPermission } from '@shared/auth/permissions';
import { ActionButton } from '@shared/components/ActionButton';
import { RequiredFieldLabel } from '@shared/components/forms/RequiredFieldLabel';
import { ValidatedTextField } from '@shared/components/forms/ValidatedTextField';
import { formatRuPhone } from '@shared/lib/phone';
import { dialogContentSx, dialogPaperSx } from '@shared/ui/dialogSurface';
import { sectionTitleSx } from '@shared/theme/sectionTitleSx';
import { useToastMessageEffect } from '@shared/ui/toasts';
import { useIsMobileViewport } from '@shared/lib/responsive';
import { employeePersonLabels, type UserTab } from '../model/constants';
import { useAdminPage, type AdminUserFormValues } from '../model/useAdminPage';

const inputFieldSx = {
  '& .MuiOutlinedInput-root': {
    borderRadius: 1,
    backgroundColor: 'background.paper'
  }
};

export const AdminPageView = () => {
  const { session } = useAuth();
  const theme = useTheme();
  const isMobileViewport = useIsMobileViewport();
  const [isInviteDialogOpen, setIsInviteDialogOpen] = useState(false);
  const {
    isLeadLike,
    canViewRoleIds,
    isDialogOpen,
    openCreateDialog,
    activeTab,
    handleTabChange,
    users,
    contractors,
    isLoadingUsers,
    usersError,
    canUpdateStatus,
    canUpdateRole,
    roleUpdateOptions,
    roleOptions,
    userTabs,
    getRoleLabel,
    canOpenCreateDialog,
    canAssignUnitOnCreate,
    canShowUnitOnCreate,
    isContractorRole,
    isLoadingUnitOptions,
    loadUsers,
    handleClose,
    onSubmit,
    form,
    unitOptions,
  } = useAdminPage();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting, touchedFields, dirtyFields, submitCount }
  } = form;

  const selectedRoleId = watch('role_id');
  const selectedUnitId = watch('unit_id');
  const loginValue = watch('login');
  const mailValue = watch('mail');
  const companyNameValue = watch('company_name');
  const innValue = watch('inn');
  const companyPhoneValue = watch('company_phone');
  const isEmployeesTab = activeTab !== 'contractors';
  const handleRoleSelectChange = (event: SelectChangeEvent<UserTab>) => {
    handleTabChange(event.target.value as UserTab);
  };

  const companyPhoneRegistration = register('company_phone');
  const phoneRegistration = register('phone');
  const touchedMap = touchedFields as Partial<Record<keyof AdminUserFormValues, unknown>>;
  const dirtyMap = dirtyFields as Partial<Record<keyof AdminUserFormValues, unknown>>;
  const getFieldError = (field: keyof AdminUserFormValues) => {
    const shouldShow = submitCount > 0 || Boolean(touchedMap[field]) || Boolean(dirtyMap[field]);
    const message = errors[field]?.message;
    if (!shouldShow || typeof message !== 'string') {
      return undefined;
    }
    return message;
  };
  const hasValue = (value: string | undefined) => Boolean(value?.trim());
  const isRoleFieldValid = selectedRoleId > 0 && !errors.role_id;
  const isLoginFieldValid = hasValue(loginValue) && !errors.login;
  const isMailFieldValid = hasValue(mailValue) && !errors.mail;
  const isCompanyNameFieldValid = hasValue(companyNameValue) && !errors.company_name;
  const isInnFieldValid = hasValue(innValue) && !errors.inn;
  const isCompanyPhoneFieldValid = hasValue(companyPhoneValue) && !errors.company_phone;
  const selectedUnitOption = unitOptions.find((option) => option.unitId === selectedUnitId) ?? null;
  const canInviteContractors = activeTab === 'contractors' && hasPermission(session, 'users.registration.invite');

  const breadcrumbActions = useMemo(
    () => {
      if (!canInviteContractors) {
        return null;
      }
      if (isMobileViewport) {
        return (
          <ActionButton
            kind="outlined"
            aria-label="Пригласить"
            onClick={() => setIsInviteDialogOpen(true)}
            sx={{
              minHeight: 42,
              height: 42,
              width: 42,
              minWidth: 42,
              px: 0,
              gap: 0,
              justifyContent: 'center',
              borderRadius: `${theme.acomShape.buttonRadius}px !important`,
              '& .MuiButton-startIcon': { margin: 0 },
            }}
            showNavigationIcons={false}
            startIcon={<ForwardToInboxOutlined fontSize="small" />}
          />
        );
      }
      return (
        <Button
          variant="outlined"
          onClick={() => setIsInviteDialogOpen(true)}
          startIcon={<ForwardToInboxOutlined fontSize="small" />}
          sx={{ textTransform: 'none' }}
        >
          Пригласить
        </Button>
      );
    },
    [canInviteContractors, isMobileViewport, theme]
  );

  useSetPageBreadcrumbActions(breadcrumbActions);

  useToastMessageEffect({ message: usersError });

  return (
    <Stack spacing={2}>
      {!isLeadLike ? (
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
      {activeTab === 'contractors' ? (
        <ContractorsListView
          contractors={contractors}
          isLoading={isLoadingUsers}
          emptyMessage="Список пользователей пока пуст."
          onStatusUpdated={loadUsers}
          onAddClick={canOpenCreateDialog ? openCreateDialog : undefined}
        />
      ) : (
        <UsersTable
          users={users}
          isLoading={isLoadingUsers}
          emptyMessage={isEmployeesTab ? employeePersonLabels.emptyList : 'Список пользователей пока пуст.'}
          getRoleLabel={getRoleLabel}
          isContractorsTab={false}
          canViewRoleIds={canViewRoleIds}
          canUpdateStatus={canUpdateStatus}
          canUpdateRole={canUpdateRole}
          allowedRoleOptions={roleUpdateOptions}
          onStatusUpdated={loadUsers}
          onAddClick={canOpenCreateDialog ? openCreateDialog : undefined}
        />
      )}

      <Dialog
        open={isDialogOpen}
        onClose={handleClose}
        maxWidth={isContractorRole ? 'lg' : 'sm'}
        fullWidth
        PaperProps={{ sx: dialogPaperSx }}
      >
        <DialogContent sx={{ ...dialogContentSx, display: 'flex', gap: 3, alignItems: 'flex-start', flexWrap: { xs: 'wrap', md: 'nowrap' } }}>
          <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ flex: 1, minWidth: 0 }}>
            <Stack spacing={2}>
              <Typography variant="h5" fontWeight={600} lineHeight={1}>
                {isContractorRole
                  ? 'Создание контрагента'
                  : isEmployeesTab
                    ? employeePersonLabels.createDialogTitle
                    : 'Создание нового пользователя'}
              </Typography>
              <TextField
                label={
                  <RequiredFieldLabel
                    label={isEmployeesTab && !isContractorRole ? employeePersonLabels.roleFieldLabel : 'Роль пользователя'}
                    isValid={isRoleFieldValid}
                  />
                }
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
                  <Typography sx={sectionTitleSx}>
                    Данные для регистрации
                  </Typography>
                  <ValidatedTextField
                    label={<RequiredFieldLabel label="Наименование компании" isValid={isCompanyNameFieldValid} />}
                    fieldName="company_name"
                    error={Boolean(getFieldError('company_name'))}
                    helperText={getFieldError('company_name')}
                    registration={register('company_name')}
                    sx={inputFieldSx}
                  />
                  <ValidatedTextField
                    label={<RequiredFieldLabel label="ИНН" isValid={isInnFieldValid} />}
                    fieldName="inn"
                    error={Boolean(getFieldError('inn'))}
                    helperText={getFieldError('inn')}
                    registration={register('inn')}
                    sx={inputFieldSx}
                  />
                  <ValidatedTextField
                    label={<RequiredFieldLabel label="Телефон компании" isValid={isCompanyPhoneFieldValid} />}
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
                  <Typography sx={sectionTitleSx}>
                    Данные для входа
                  </Typography>
                  <ValidatedTextField
                    label={<RequiredFieldLabel label="Логин" isValid={isLoginFieldValid} />}
                    fieldName="login"
                    error={Boolean(getFieldError('login'))}
                    helperText={getFieldError('login')}
                    registration={register('login')}
                    sx={inputFieldSx}
                  />
                  <ValidatedTextField
                    label={<RequiredFieldLabel label="E-mail" isValid={isMailFieldValid} />}
                    fieldName="mail"
                    error={Boolean(getFieldError('mail'))}
                    helperText={getFieldError('mail')}
                    registration={register('mail')}
                    sx={inputFieldSx}
                  />

                  <Typography sx={sectionTitleSx}>
                    {employeePersonLabels.profileSectionTitle}
                  </Typography>
                  <ValidatedTextField
                    label="ФИО"
                    fieldName="full_name"
                    error={Boolean(getFieldError('full_name'))}
                    helperText={getFieldError('full_name')}
                    registration={register('full_name')}
                    sx={inputFieldSx}
                  />
                  <ValidatedTextField
                    label="Телефон"
                    fieldName="phone"
                    placeholder="+7 (900) 999-88-77"
                    error={Boolean(getFieldError('phone'))}
                    helperText={getFieldError('phone')}
                    name={phoneRegistration.name}
                    inputRef={phoneRegistration.ref}
                    onBlur={phoneRegistration.onBlur}
                    onChange={(event) => {
                      const formatted = formatRuPhone(event.target.value);
                      setValue('phone', formatted, {
                        shouldDirty: true,
                        shouldTouch: true,
                        shouldValidate: true
                      });
                    }}
                    sx={inputFieldSx}
                  />

                  {canShowUnitOnCreate && unitOptions.length > 0 ? (
                    <>
                      <Typography sx={sectionTitleSx}>
                        Объединение
                      </Typography>
                      <Autocomplete
                        loading={isLoadingUnitOptions}
                        options={unitOptions}
                        value={selectedUnitOption}
                        onChange={(_event, value) => {
                          setValue('unit_id', value?.unitId ?? null, {
                            shouldDirty: true,
                            shouldTouch: true,
                            shouldValidate: true,
                          });
                        }}
                        getOptionLabel={(option) => option.label}
                        isOptionEqualToValue={(option, value) => option.unitId === value.unitId}
                        renderInput={(params) => (
                          <TextField
                            {...params}
                            label="Объединение"
                            placeholder="Выберите объединение"
                            helperText={
                              canAssignUnitOnCreate
                                ? 'Необязательно. Можно назначить сразу при создании.'
                                : 'По умолчанию выбрано ваше подразделение. Можно изменить перед созданием.'
                            }
                            sx={inputFieldSx}
                          />
                        )}
                      />
                    </>
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
                    : isEmployeesTab
                      ? employeePersonLabels.createSubmitLabel
                      : 'Создать пользователя'}
              </Button>
            </Stack>
          </Box>
          {isContractorRole ? (
            <ManualContractorDuplicatePanel
              open={isDialogOpen}
              companyName={companyNameValue}
              inn={innValue}
              companyMail={watch('company_mail')}
            />
          ) : null}
        </DialogContent>
      </Dialog>

      <ContractorInviteDialog
        open={isInviteDialogOpen}
        onClose={() => setIsInviteDialogOpen(false)}
      />
    </Stack>
  );
};
