import { ROLE } from '@shared/constants/roles';

export type UserTab =
  | 'contractors'
  | 'admins'
  | 'economists'
  | 'lead_economists'
  | 'project_managers'
  | 'operators';

export const roleByTab: Record<UserTab, number> = {
  contractors: ROLE.CONTRACTOR,
  admins: ROLE.ADMIN,
  economists: ROLE.ECONOMIST,
  lead_economists: ROLE.LEAD_ECONOMIST,
  project_managers: ROLE.PROJECT_MANAGER,
  operators: ROLE.OPERATOR
};

export const tabOptions: Array<{ value: UserTab; label: string }> = [
  { value: 'contractors', label: 'Контрагенты' },
  { value: 'admins', label: 'Администраторы' },
  { value: 'economists', label: 'Экономисты' },
  { value: 'lead_economists', label: 'Ведущие экономисты' },
  { value: 'project_managers', label: 'Руководители проекта' },
  { value: 'operators', label: 'Операторы' }
];

export const roleLabelsById: Record<number, string> = {
  1: 'Суперадмин',
  2: 'Администратор',
  3: 'Контрагент',
  4: 'Руководитель проекта',
  5: 'Ведущий экономист',
  6: 'Экономист',
  7: 'Оператор'
};

export const addUserButtonSx = {
  borderRadius: 999,
  textTransform: 'none',
  px: 3,
  minWidth: 220,
  whiteSpace: 'nowrap'
};

export const employeePersonLabels = {
  searchPlaceholder: 'Найти сотрудника',
  addButtonLabel: 'Добавить сотрудника',
  emptyList: 'Список сотрудников пока пуст.',
  cardTitle: 'Карточка сотрудника',
  detailsToggle: 'Детали сотрудника',
  userSectionTitle: 'Сотрудник',
  profileSectionTitle: 'Профиль сотрудника',
  createDialogTitle: 'Создание нового сотрудника',
  roleFieldLabel: 'Роль сотрудника',
  createSubmitLabel: 'Создать сотрудника',
  loadListError: 'Не удалось загрузить список сотрудников',
  createError: 'Не удалось создать сотрудника',
} as const;
