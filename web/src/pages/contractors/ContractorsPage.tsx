import ForwardToInboxOutlined from '@mui/icons-material/ForwardToInboxOutlined';
import { Button, Stack } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSetPageBreadcrumbActions } from '@app/layouts/PageBreadcrumbActions';
import { useAuth } from '@app/providers/AuthProvider';
import { ContractorCreateDialog } from '@features/contractors/components/ContractorCreateDialog';
import { ContractorInviteDialog } from '@features/contractors/components/ContractorInviteDialog';
import { ContractorsListView } from '@features/contractors/components/ContractorsListView';
import { listContractors } from '@shared/api/contractors/listContractors';
import { hasPermission } from '@shared/auth/permissions';
import { ActionButton } from '@shared/components/ActionButton';
import { useIsMobileViewport } from '@shared/lib/responsive';
import { useSystemToasts } from '@shared/ui/toasts';

export const ContractorsPage = () => {
  const { session } = useAuth();
  const theme = useTheme();
  const isMobileViewport = useIsMobileViewport();
  const { showErrorToast } = useSystemToasts();
  const [contractors, setContractors] = useState<Awaited<ReturnType<typeof listContractors>>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isInviteDialogOpen, setIsInviteDialogOpen] = useState(false);

  const canManageContractors = hasPermission(session, 'contractors.manual.create');
  const canInviteContractors = hasPermission(session, 'users.registration.invite');

  const breadcrumbActions = useMemo(
    () =>
      canInviteContractors ? (
        isMobileViewport ? (
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
              '& .MuiButton-startIcon': {
                margin: 0
              }
            }}
            showNavigationIcons={false}
            startIcon={<ForwardToInboxOutlined fontSize="small" />}
          />
        ) : (
          <Button
            variant="outlined"
            onClick={() => setIsInviteDialogOpen(true)}
            startIcon={<ForwardToInboxOutlined fontSize="small" />}
            sx={{ textTransform: 'none' }}
          >
            Пригласить
          </Button>
        )
      ) : null,
    [canInviteContractors, isMobileViewport, theme]
  );

  useSetPageBreadcrumbActions(breadcrumbActions);

  const loadContractors = useCallback(async () => {
    setIsLoading(true);
    try {
      const items = await listContractors();
      setContractors(items);
    } catch (loadError) {
      setContractors([]);
      showErrorToast(loadError instanceof Error ? loadError.message : 'Не удалось загрузить контрагентов');
    } finally {
      setIsLoading(false);
    }
  }, [showErrorToast]);

  useEffect(() => {
    void loadContractors();
  }, [loadContractors]);

  return (
    <Stack spacing={2}>
      <ContractorsListView
        contractors={contractors}
        isLoading={isLoading}
        emptyMessage="Контрагенты не найдены"
        onStatusUpdated={loadContractors}
        onAddClick={canManageContractors ? () => setIsCreateDialogOpen(true) : undefined}
      />
      <ContractorCreateDialog
        open={isCreateDialogOpen}
        onClose={() => setIsCreateDialogOpen(false)}
        onCreated={loadContractors}
      />
      <ContractorInviteDialog
        open={isInviteDialogOpen}
        onClose={() => setIsInviteDialogOpen(false)}
      />
    </Stack>
  );
};
