import type { UserActions } from '@shared/api/mappers';

export type UserListItem = {
  user_id: string;
  role_id: number;
  id_parent: string | null;
  status: string;
  full_name: string | null;
  phone: string | null;
  mail: string | null;
  company_name: string | null;
  inn: string | null;
  company_phone: string | null;
  company_mail: string | null;
  address: string | null;
  note: string | null;
  actions: UserActions;
};
