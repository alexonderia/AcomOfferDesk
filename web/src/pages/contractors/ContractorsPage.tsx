import { Alert, Button, Stack } from '@mui/material';
import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '@app/providers/AuthProvider';
import { ContractorInviteDialog } from '@features/contractors/components/ContractorInviteDialog';
import { ContractorsListView } from '@features/contractors/components/ContractorsListView';
import type { UserListItem } from '@entities/user';
import { listContractors } from '@shared/api/contractors/listContractors';
import { hasPermission } from '@shared/auth/permissions';

const mapContractorToUserListItem = (item: Awaited<ReturnType<typeof listContractors>>[number]): UserListItem => ({
  user_id: item.userId,
  role_id: item.roleId,
  id_parent: null,
  status: item.status,
  full_name: item.fullName,
  phone: item.phone,
  mail: item.mail,
  company_name: item.companyName,
  inn: item.inn,
  company_phone: item.companyPhone,
  company_mail: item.companyMail,
  address: item.address,
  note: item.note,
  actions: item.actions,
});

export const ContractorsPage = () => {
  const { session } = useAuth();
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInviteDialogOpen, setIsInviteDialogOpen] = useState(false);

  const canInviteContractors = hasPermission(session, 'contractors.manual.create');

  const loadContractors = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const items = await listContractors();
      setUsers(items.map(mapContractorToUserListItem));
    } catch (loadError) {
      setUsers([]);
      setError(loadError instanceof Error ? loadError.message : 'Не удалось загрузить контрагентов');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadContractors();
  }, [loadContractors]);

  return (
    <Stack spacing={2}>
      {error ? <Alert severity="error">{error}</Alert> : null}
      {canInviteContractors ? (
        <Stack direction="row" justifyContent="flex-end">
          <Button variant="outlined" onClick={() => setIsInviteDialogOpen(true)}>
            Пригласить контрагента
          </Button>
        </Stack>
      ) : null}
      <ContractorsListView
        users={users}
        isLoading={isLoading}
        emptyMessage="Контрагенты не найдены"
        onStatusUpdated={loadContractors}
        useContractorsStatusApi
      />
      <ContractorInviteDialog
        open={isInviteDialogOpen}
        onClose={() => setIsInviteDialogOpen(false)}
      />
    </Stack>
  );
};
