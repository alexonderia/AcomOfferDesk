export type DelegationAccessSource = {
  code: string;
  enabled: boolean;
  grantedViaRole: boolean;
  grantedIndividually: boolean;
};

export const permissionSourceLabel = (
  grantedViaRole: boolean,
  grantedIndividually: boolean
): string => {
  if (grantedViaRole && grantedIndividually) {
    return 'Через роль + индивидуально';
  }
  if (grantedViaRole) {
    return 'Через роль';
  }
  if (grantedIndividually) {
    return 'Индивидуально';
  }
  return 'Отсутствует';
};

export const withIndividualGrant = <T extends DelegationAccessSource>(
  access: T,
  grantedIndividually: boolean
): T => ({
  ...access,
  grantedIndividually,
  enabled: access.grantedViaRole || grantedIndividually,
});

export const getIndividuallyGrantedAccessCodes = (
  accesses: DelegationAccessSource[]
): string[] => accesses
  .filter((item) => item.grantedIndividually)
  .map((item) => item.code);
