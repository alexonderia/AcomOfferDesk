type PermissionCarrier = {
  permissions?: string[];
} | null | undefined;

export const hasPermission = (carrier: PermissionCarrier, permission: string): boolean =>
  Boolean(carrier?.permissions?.includes(permission));

export const hasAnyPermission = (carrier: PermissionCarrier, permissions: string[]): boolean =>
  permissions.some((permission) => hasPermission(carrier, permission));
