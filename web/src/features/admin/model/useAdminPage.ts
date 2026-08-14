import { zodResolver } from '@hookform/resolvers/zod';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useLiveValidatedForm } from '@shared/lib/forms';
import { useSearchParams } from 'react-router-dom';
import { z } from 'zod';
import { useAuth } from '@app/providers/AuthProvider';
import { mapUserListItemToContractorListItem } from '@features/contractors/lib/mapUserListItemToContractorListItem';
import type { UserListItem } from '@entities/user';
import { listContractors } from '@shared/api/contractors/listContractors';
import type { ContractorListItem } from '@shared/api/contractors/listContractors';
import { registerUser } from '@shared/api/auth/registerUser';
import { createManualContractor } from '@shared/api/users/createManualContractor';
import { getUsers } from '@shared/api/users/getUsers';
import { getUnitsTree } from '@shared/api/units';
import { hasAnyPermission, hasPermission } from '@shared/auth/permissions';
import { ROLE } from '@shared/constants/roles';
import { isValidRuPhone } from '@shared/lib/phone';
import { buildUnitOptions, type UnitOption } from '@shared/lib/hierarchy/buildUnitOptions';
import { addUserButtonSx, employeePersonLabels, roleByTab, roleLabelsById, tabOptions, type UserTab } from './constants';
import { getScopedCreateRoleIds, resolveUserTabFromParam } from './helpers';
import { useSystemToasts } from '@shared/ui/toasts';

const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const innRegex = /^\d{10}$|^\d{12}$/;

const schema = z
  .object({
    role_id: z.number({ required_error: 'Выберите роль' }),
    login: z.string().optional(),
    password: z.string().optional(),
    confirmPassword: z.string().optional(),
    mail: z.string().optional(),
    full_name: z.string().optional(),
    phone: z.string().optional(),
    company_name: z.string().optional(),
    inn: z.string().optional(),
    company_phone: z.string().optional(),
    company_mail: z.string().optional(),
    address: z.string().optional(),
    note: z.string().optional(),
    unit_id: z.number().nullable().optional(),
  })
  .superRefine((data, ctx) => {
    const isContractor = data.role_id === ROLE.CONTRACTOR;

    if (isContractor) {
      const companyName = data.company_name?.trim() ?? '';
      const inn = data.inn?.trim() ?? '';
      const companyPhone = data.company_phone?.trim() ?? '';
      const companyMail = data.company_mail?.trim() ?? '';
      const address = data.address?.trim() ?? '';
      const note = data.note?.trim() ?? '';

      if (!companyName) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Наименование компании обязательно',
          path: ['company_name']
        });
      } else if (companyName.length > 256) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Наименование компании не должно превышать 256 символов',
          path: ['company_name']
        });
      }

      if (!inn) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'ИНН обязателен',
          path: ['inn']
        });
      } else if (!innRegex.test(inn)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'ИНН должен содержать 10 или 12 цифр',
          path: ['inn']
        });
      }

      if (!companyPhone) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Телефон компании обязателен',
          path: ['company_phone']
        });
      } else if (!isValidRuPhone(companyPhone)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Некорректный формат телефона компании',
          path: ['company_phone']
        });
      }

      if (companyMail && !emailRegex.test(companyMail)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Некорректный формат e-mail компании',
          path: ['company_mail']
        });
      }

      if (address.length > 256) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Адрес не должен превышать 256 символов',
          path: ['address']
        });
      }

      if (note.length > 1024) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Дополнительная информация не должна превышать 1024 символа',
          path: ['note']
        });
      }

      return;
    }

    const login = data.login?.trim() ?? '';
    const mail = data.mail?.trim() ?? '';
    const fullName = data.full_name?.trim() ?? '';
    const phone = data.phone?.trim() ?? '';

    if (login.length < 3) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Минимум 3 символа',
        path: ['login']
      });
    }

    if (!mail) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'E-mail обязателен для будущей привязки учётной записи',
        path: ['mail']
      });
    } else if (!emailRegex.test(mail)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Некорректный формат e-mail',
        path: ['mail']
      });
    }

    if (fullName && fullName.length > 256) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'ФИО не должно превышать 256 символов',
        path: ['full_name']
      });
    }

    if (phone && !isValidRuPhone(phone)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Некорректный формат телефона',
        path: ['phone']
      });
    } else if (phone.length > 64) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Телефон не должен превышать 64 символа',
        path: ['phone']
      });
    }

  });

export type AdminUserFormValues = z.infer<typeof schema>;

export const useAdminPage = () => {
  const { session } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const isLeadEconomist = session?.roleId === ROLE.LEAD_ECONOMIST;
  const isProjectManager = session?.roleId === ROLE.PROJECT_MANAGER;
  const isEconomist = session?.roleId === ROLE.ECONOMIST;
  const isLeadLike = isLeadEconomist || isProjectManager || isEconomist;
  const isAdmin = session?.roleId === ROLE.ADMIN;
  const canCreateManualContractor = hasPermission(session, 'contractors.manual.create');
  const canCreateUser = hasPermission(session, 'users.create');
  const canAssignUnitOnCreate = hasPermission(session, 'units.members.manage')
    && hasPermission(session, 'units.read');
  const canShowUnitOnCreate = canCreateUser && hasPermission(session, 'units.read');
  const canUpdateRoleAny = hasPermission(session, 'users.role.update_any');
  const canUpdateRoleEconomy = hasPermission(session, 'users.role.update_economy');
  const canUpdateStatus = hasPermission(session, 'users.status.update');
  const canUpdateRole = canUpdateRoleAny || canUpdateRoleEconomy;
  const canViewRoleIds = hasAnyPermission(session, ['users.role.update_any', 'users.role.update_economy']);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<UserTab>(() =>
    isLeadLike ? 'economists' : resolveUserTabFromParam(searchParams.get('users_tab'))
  );
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [contractors, setContractors] = useState<ContractorListItem[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [usersError, setUsersError] = useState<string | null>(null);
  const [unitOptions, setUnitOptions] = useState<UnitOption[]>([]);
  const [isLoadingUnitOptions, setIsLoadingUnitOptions] = useState(false);
  const loadUsersRequestIdRef = useRef(0);

  const baseCreateRoleIds = useMemo(() => {
    const roleIds: number[] = [];
    const addRole = (roleId: number) => {
      if (!roleIds.includes(roleId)) {
        roleIds.push(roleId);
      }
    };

    if (canCreateUser) {
      if (session?.roleId === ROLE.SUPERADMIN) {
        [ROLE.ADMIN, ROLE.SECURITY_OFFICER, ROLE.PROJECT_MANAGER, ROLE.LEAD_ECONOMIST, ROLE.ECONOMIST, ROLE.OPERATOR].forEach(addRole);
      } else if (session?.roleId === ROLE.ADMIN) {
        [ROLE.ECONOMIST, ROLE.OPERATOR].forEach(addRole);
      } else if (session?.roleId === ROLE.LEAD_ECONOMIST) {
        [ROLE.ECONOMIST].forEach(addRole);
      }
    }

    if (canCreateManualContractor) {
      addRole(ROLE.CONTRACTOR);
    }

    return roleIds;
  }, [canCreateManualContractor, canCreateUser, session?.roleId]);

  const roleOptions = useMemo(() => {
    const scopedRoleIds = getScopedCreateRoleIds({
      activeTab,
      availableRoleIds: baseCreateRoleIds,
      sessionRoleId: session?.roleId
    });

    return scopedRoleIds.map((roleId) => ({ id: roleId, label: roleLabelsById[roleId] }));
  }, [activeTab, baseCreateRoleIds, session?.roleId]);

  const canOpenCreateDialog = roleOptions.length > 0;
  const preferredCreateRoleId = roleOptions[0]?.id ?? roleByTab[activeTab];

  const roleUpdateOptions = useMemo(() => {
    if (canUpdateRoleAny) {
      return [
        ROLE.ADMIN,
        ROLE.CONTRACTOR,
        ROLE.SECURITY_OFFICER,
        ROLE.PROJECT_MANAGER,
        ROLE.LEAD_ECONOMIST,
        ROLE.ECONOMIST,
        ROLE.OPERATOR
      ];
    }
    if (!canUpdateRoleEconomy) {
      return [];
    }
    if (session?.roleId === ROLE.PROJECT_MANAGER) {
      return [ROLE.LEAD_ECONOMIST, ROLE.ECONOMIST, ROLE.OPERATOR];
    }
    if (session?.roleId === ROLE.LEAD_ECONOMIST) {
      return [ROLE.ECONOMIST, ROLE.OPERATOR];
    }
    return [];
  }, [canUpdateRoleAny, canUpdateRoleEconomy, session?.roleId]);

  const userTabs = useMemo(() => {
    if (isLeadLike) return tabOptions.filter((tab) => tab.value === 'economists');
    return tabOptions;
  }, [isLeadLike]);

  const getRoleLabel = useCallback((roleId: number) => roleLabelsById[roleId] ?? `Роль ${roleId}`, []);
  const { showErrorToast, showSuccessToast } = useSystemToasts();

  const form = useLiveValidatedForm<AdminUserFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      role_id: preferredCreateRoleId,
      login: '',
      password: '',
      confirmPassword: '',
      mail: '',
      full_name: '',
      phone: '',
      company_name: '',
      inn: '',
      company_phone: '',
      company_mail: '',
      address: '',
      note: '',
      unit_id: null,
    }
  });

  const { watch, setValue, reset } = form;
  const selectedRoleId = watch('role_id');
  const isContractorRole = selectedRoleId === ROLE.CONTRACTOR;

  const handleTabChange = (value: UserTab) => {
    setActiveTab(value);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('users_tab', value);
      return next;
    }, { replace: true });
  };

  useEffect(() => {
    if (!isDialogOpen || !canShowUnitOnCreate || selectedRoleId === ROLE.CONTRACTOR) {
      return undefined;
    }

    let cancelled = false;
    setIsLoadingUnitOptions(true);

    void getUnitsTree()
      .then((tree) => {
        if (cancelled) {
          return;
        }
        const options = buildUnitOptions(tree);
        setUnitOptions(options);
        if (isLeadLike && options.length > 0) {
          const defaultOption = options.reduce((best, option) =>
            option.label.split(' / ').length >= best.label.split(' / ').length ? option : best
          );
          setValue('unit_id', defaultOption.unitId, {
            shouldDirty: false,
            shouldTouch: false,
            shouldValidate: true,
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setUnitOptions([]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoadingUnitOptions(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [canShowUnitOnCreate, isDialogOpen, isLeadLike, selectedRoleId, setValue]);

  useEffect(() => {
    if (!roleOptions.length) {
      return;
    }
    const availableRoleIds = roleOptions.map((role) => role.id);
    if (!availableRoleIds.includes(selectedRoleId)) {
      setValue('role_id', roleOptions[0].id, { shouldDirty: false, shouldTouch: false, shouldValidate: true });
    }
  }, [roleOptions, selectedRoleId, setValue]);

  useEffect(() => {
    if (isLeadLike) {
      setActiveTab('economists');
    }
  }, [isLeadLike]);

  useEffect(() => {
    if (!isLeadLike) {
      setActiveTab(resolveUserTabFromParam(searchParams.get('users_tab')));
    }
  }, [isLeadLike, searchParams]);

  const loadUsers = useCallback(async () => {
    const requestId = loadUsersRequestIdRef.current + 1;
    loadUsersRequestIdRef.current = requestId;
    setIsLoadingUsers(true);
    setUsersError(null);
    try {
      if (!isLeadLike && activeTab === 'contractors') {
        const items = hasPermission(session, 'contractors.read')
          ? await listContractors()
          : (await getUsers(roleByTab.contractors)).items.map(mapUserListItemToContractorListItem);
        if (loadUsersRequestIdRef.current !== requestId) {
          return;
        }
        setContractors(items);
        setUsers([]);
      } else {
        const response = await getUsers(isLeadLike ? undefined : roleByTab[activeTab]);
        if (loadUsersRequestIdRef.current !== requestId) {
          return;
        }
        setUsers(response.items);
        setContractors([]);
      }
      setUsersError(null);
    } catch (error) {
      if (loadUsersRequestIdRef.current !== requestId) {
        return;
      }
      setUsersError(
        error instanceof Error
          ? error.message
          : activeTab === 'contractors'
            ? 'Не удалось загрузить список пользователей'
            : employeePersonLabels.loadListError
      );
    } finally {
      if (loadUsersRequestIdRef.current === requestId) {
        setIsLoadingUsers(false);
      }
    }
  }, [activeTab, isLeadLike, session]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  const resetForm = useCallback(() => {
    reset({
      role_id: preferredCreateRoleId,
      login: '',
      password: '',
      confirmPassword: '',
      mail: '',
      full_name: '',
      phone: '',
      company_name: '',
      inn: '',
      company_phone: '',
      company_mail: '',
      address: '',
      note: '',
      unit_id: null,
    });
  }, [preferredCreateRoleId, reset]);

  const openCreateDialog = useCallback(() => {
    resetForm();
    setIsDialogOpen(true);
  }, [resetForm]);

  useEffect(() => {
    if (!canOpenCreateDialog) return;

    if (searchParams.get('create') === '1') {
      openCreateDialog();
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.delete('create');
        return next;
      }, { replace: true });
    }
  }, [canOpenCreateDialog, openCreateDialog, searchParams, setSearchParams]);

  const handleClose = () => {
    setIsDialogOpen(false);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete('create');
      return next;
    }, { replace: true });
    resetForm();
  };

  const onSubmit = async (values: AdminUserFormValues) => {
    try {
      if (values.role_id === ROLE.CONTRACTOR) {
        const response = await createManualContractor({
          company_name: values.company_name?.trim() ?? '',
          inn: values.inn?.trim() ?? '',
          company_phone: values.company_phone?.trim() ?? '',
          company_mail: values.company_mail?.trim() || undefined,
          address: values.address?.trim() || undefined,
          note: values.note?.trim() || undefined
        });

        showSuccessToast(`Контрагент ${response.userId} создан.`);
      } else {
        const response = await registerUser({
          login: values.login?.trim() ?? '',
          role_id: values.role_id,
          mail: values.mail?.trim() || undefined,
          full_name: values.full_name?.trim() || undefined,
          phone: values.phone?.trim() || undefined,
          unit_id: values.unit_id ?? undefined,
        });

        showSuccessToast(`Сотрудник ${response.data.user_id} создан.`);
      }

      resetForm();
      await loadUsers();
    } catch (error) {
      showErrorToast(
        error instanceof Error
          ? error.message
          : values.role_id === ROLE.CONTRACTOR
            ? 'Не удалось создать контрагента'
            : employeePersonLabels.createError
      );
    }
  };

  return {
    isLeadLike,
    isAdmin,
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
    canCreateUser,
    canCreateManualContractor,
    canAssignUnitOnCreate,
    canShowUnitOnCreate,
    canOpenCreateDialog,
    isContractorRole,
    isLoadingUnitOptions,
    loadUsers,
    handleClose,
    onSubmit,
    form,
    unitOptions,
    addUserButtonSx
  };
};
