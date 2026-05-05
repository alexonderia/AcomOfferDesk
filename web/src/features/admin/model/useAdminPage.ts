import { zodResolver } from '@hookform/resolvers/zod';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useSearchParams } from 'react-router-dom';
import { z } from 'zod';
import { useAuth } from '@app/providers/AuthProvider';
import type { UserListItem } from '@entities/user';
import { registerUser } from '@shared/api/auth/registerUser';
import { createManualContractor } from '@shared/api/users/createManualContractor';
import { getManagerCandidates } from '@shared/api/users/getManagerCandidates';
import { getUsers } from '@shared/api/users/getUsers';
import { hasPermission } from '@shared/auth/permissions';
import { ROLE } from '@shared/constants/roles';
import { isValidRuPhone } from '@shared/lib/phone';
import { addUserButtonSx, roleByTab, roleLabelsById, tabOptions, type UserTab } from './constants';
import { resolveUserTabFromParam } from './helpers';

const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const innRegex = /^\d{10}$|^\d{12}$/;

const schema = z
  .object({
    role_id: z.number({ required_error: 'Выберите роль' }),
    login: z.string().optional(),
    password: z.string().optional(),
    confirmPassword: z.string().optional(),
    mail: z.string().optional(),
    id_parent: z.string().optional(),
    company_name: z.string().optional(),
    inn: z.string().optional(),
    company_phone: z.string().optional(),
    company_mail: z.string().optional(),
    address: z.string().optional(),
    note: z.string().optional()
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

    if (login.length < 3) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Минимум 3 символа',
        path: ['login']
      });
    }

    if (false) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Минимум 6 символов',
        path: ['password']
      });
    }

    if (false) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Минимум 6 символов',
        path: ['confirmPassword']
      });
    }

    if (false) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Пароли не совпадают',
        path: ['confirmPassword']
      });
    }

    if (!mail) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'E-mail обязателен для входа через Keycloak',
        path: ['mail']
      });
    } else if (!emailRegex.test(mail)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Некорректный формат e-mail',
        path: ['mail']
      });
    }

    if ((data.role_id === ROLE.ECONOMIST || data.role_id === ROLE.LEAD_ECONOMIST) && !data.id_parent?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Выберите руководителя',
        path: ['id_parent']
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
  const isSuperadmin = session?.roleId === ROLE.SUPERADMIN;
  const canViewRoleIds = isAdmin || isSuperadmin;
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<UserTab>(() =>
    isLeadLike ? 'economists' : resolveUserTabFromParam(searchParams.get('users_tab'))
  );
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [usersError, setUsersError] = useState<string | null>(null);
  const [canUpdateStatus, setCanUpdateStatus] = useState(false);
  const [canUpdateRole, setCanUpdateRole] = useState(false);
  const [economistAndLeadManagers, setEconomistAndLeadManagers] = useState<UserListItem[]>([]);
  const [projectManagerManagers, setProjectManagerManagers] = useState<UserListItem[]>([]);

  const roleOptions = useMemo(() => {
    if (isLeadLike) {
      return [{ id: ROLE.ECONOMIST, label: roleLabelsById[ROLE.ECONOMIST] }];
    }

    if (session?.roleId === ROLE.SUPERADMIN) {
      return [
        { id: ROLE.ADMIN, label: roleLabelsById[ROLE.ADMIN] },
        { id: ROLE.CONTRACTOR, label: roleLabelsById[ROLE.CONTRACTOR] },
        { id: ROLE.PROJECT_MANAGER, label: roleLabelsById[ROLE.PROJECT_MANAGER] },
        { id: ROLE.LEAD_ECONOMIST, label: roleLabelsById[ROLE.LEAD_ECONOMIST] },
        { id: ROLE.ECONOMIST, label: roleLabelsById[ROLE.ECONOMIST] },
        { id: ROLE.OPERATOR, label: roleLabelsById[ROLE.OPERATOR] }
      ];
    }

    return [
      { id: ROLE.ECONOMIST, label: roleLabelsById[ROLE.ECONOMIST] },
      { id: ROLE.OPERATOR, label: roleLabelsById[ROLE.OPERATOR] }
    ];
  }, [isLeadLike, session?.roleId]);

  const userTabs = useMemo(() => {
    if (isLeadLike) return tabOptions.filter((tab) => tab.value === 'economists');
    if (session?.roleId === ROLE.SUPERADMIN) return tabOptions;
    return tabOptions.filter((tab) => tab.value === 'contractors' || tab.value === 'economists' || tab.value === 'admins');
  }, [isLeadLike, session?.roleId]);

  const canCreateUser = hasPermission(session, 'users.create');
  const getRoleLabel = useCallback((roleId: number) => roleLabelsById[roleId] ?? `Роль ${roleId}`, []);

  const form = useForm<AdminUserFormValues>({
    resolver: zodResolver(schema),
    mode: 'onChange',
    reValidateMode: 'onChange',
    defaultValues: {
      role_id: roleOptions[0]?.id ?? ROLE.ADMIN,
      login: '',
      password: '',
      confirmPassword: '',
      mail: '',
      id_parent: '',
      company_name: '',
      inn: '',
      company_phone: '',
      company_mail: '',
      address: '',
      note: ''
    }
  });

  const { watch, setValue, reset } = form;
  const selectedRoleId = watch('role_id');
  const isContractorRole = selectedRoleId === ROLE.CONTRACTOR;
  const requiresParent = selectedRoleId === ROLE.ECONOMIST || selectedRoleId === ROLE.LEAD_ECONOMIST;
  const managerOptions = selectedRoleId === ROLE.ECONOMIST ? economistAndLeadManagers : projectManagerManagers;

  const handleTabChange = (value: UserTab) => {
    setActiveTab(value);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('users_tab', value);
      return next;
    }, { replace: true });
  };

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

  useEffect(() => {
    if (!canCreateUser) return;

    if (searchParams.get('create') === '1') {
      setIsDialogOpen(true);
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.delete('create');
        return next;
      }, { replace: true });
    }
  }, [canCreateUser, searchParams, setSearchParams]);

  const loadManagers = useCallback(async () => {
    const [economistManagersResult, leadEconomistManagersResult] = await Promise.allSettled([
      getManagerCandidates(ROLE.ECONOMIST),
      getManagerCandidates(ROLE.LEAD_ECONOMIST)
    ]);

    setEconomistAndLeadManagers(
      economistManagersResult.status === 'fulfilled' ? economistManagersResult.value.items : []
    );
    setProjectManagerManagers(
      leadEconomistManagersResult.status === 'fulfilled' ? leadEconomistManagersResult.value.items : []
    );
  }, []);

  useEffect(() => {
    if (!isDialogOpen) return;
    void loadManagers();
  }, [isDialogOpen, loadManagers]);

  useEffect(() => {
    if (!requiresParent) {
      setValue('id_parent', '');
    }
  }, [requiresParent, setValue]);

  const loadUsers = useCallback(async () => {
    setIsLoadingUsers(true);
    setUsersError(null);
    try {
      const response = await getUsers(roleByTab[activeTab]);
      setUsers(response.items);
      setCanUpdateStatus(response.permissions.includes('users.status.update'));
      setCanUpdateRole(response.permissions.includes('users.role.update'));
    } catch (error) {
      setUsersError(error instanceof Error ? error.message : 'Не удалось загрузить список пользователей');
      setCanUpdateStatus(false);
      setCanUpdateRole(false);
    } finally {
      setIsLoadingUsers(false);
    }
  }, [activeTab]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  const resetForm = useCallback(() => {
    reset({
      role_id: roleOptions[0]?.id ?? ROLE.ADMIN,
      login: '',
      password: '',
      confirmPassword: '',
      mail: '',
      id_parent: '',
      company_name: '',
      inn: '',
      company_phone: '',
      company_mail: '',
      address: '',
      note: ''
    });
  }, [reset, roleOptions]);

  const handleClose = () => {
    setIsDialogOpen(false);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete('create');
      return next;
    }, { replace: true });
    setErrorMessage(null);
    setSuccessMessage(null);
    resetForm();
  };

  const onSubmit = async (values: AdminUserFormValues) => {
    setErrorMessage(null);
    setSuccessMessage(null);
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

        setSuccessMessage(`Контрагент ${response.userId} создан.`);
      } else {
        const response = await registerUser({
          login: values.login?.trim() ?? '',
          role_id: values.role_id,
          mail: values.mail?.trim() || undefined,
          id_parent: values.id_parent?.trim() || undefined
        });

        setSuccessMessage(`Пользователь ${response.data.user_id} создан.`);
      }

      resetForm();
      await Promise.all([loadUsers(), loadManagers()]);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Не удалось создать пользователя');
    }
  };

  return {
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
    form,
    addUserButtonSx
  };
};
