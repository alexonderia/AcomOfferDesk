import type { UserListItem } from '@entities/user';
import type { ContractorListItem } from '@shared/api/contractors/listContractors';

export const mapUserListItemToContractorListItem = (user: UserListItem): ContractorListItem => ({
  userId: user.user_id,
  roleId: user.role_id,
  status: user.status,
  fullName: user.full_name,
  phone: user.phone,
  mail: user.mail,
  companyName: user.company_name,
  inn: user.inn,
  companyPhone: user.company_phone,
  companyMail: user.company_mail,
  address: user.address,
  note: user.note,
  createdAt: null,
  updatedAt: null,
  actions: user.actions,
  rootUnits: null,
});
