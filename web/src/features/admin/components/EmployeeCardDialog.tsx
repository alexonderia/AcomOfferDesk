import { Alert, Box, Button, CircularProgress, Dialog, DialogContent, Stack, Typography } from '@mui/material';
import { useId, type ReactNode } from 'react';
import type { UserListItem } from '@entities/user';
import type { UnitNode } from '@shared/api/units';
import type { UserHierarchy } from '@shared/api/users/getUserHierarchy';
import {
  dialogContentSx, dialogPaperSx, EmailWithVerifiedMark, formatPhoneForView,
  InfoRow, SourceSection, UserStatusPill,
} from './UserCardPrimitives';
import { UserHierarchyTree } from './UserHierarchyTree';

type EmployeeCardUser = Pick<UserListItem, 'user_id' | 'status' | 'full_name' | 'phone' | 'mail' | 'email_verified'>
  & Partial<Pick<UserListItem, 'units_count' | 'managers_count' | 'subordinates_count'>>;

export const EmployeeCardDialog = ({
  open, onClose, user, error, onRetry, hierarchy, unitsTree,
  isLoadingHierarchy, hierarchyError, showEmailVerification = false, headerActions, children,
}: {
  open: boolean;
  onClose: () => void;
  user: EmployeeCardUser | null;
  error?: string | null;
  onRetry?: () => void;
  hierarchy: UserHierarchy | null;
  unitsTree: UnitNode[];
  isLoadingHierarchy: boolean;
  hierarchyError?: string | null;
  showEmailVerification?: boolean;
  headerActions?: ReactNode;
  children?: ReactNode;
}) => {
  const titleId = useId();
  const unitsCount = user?.units_count ?? (hierarchy ? hierarchy.units.length : '—');
  const managersCount = user?.managers_count ?? (hierarchy ? new Set(hierarchy.managers.map((item) => item.userId)).size : '—');
  const subordinatesCount = user?.subordinates_count ?? (hierarchy ? new Set(hierarchy.subordinates.map((item) => item.userId)).size : '—');

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth aria-labelledby={titleId}
      PaperProps={{ sx: dialogPaperSx }} onClick={(event) => event.stopPropagation()}>
      <DialogContent sx={dialogContentSx}>
        <Stack spacing={2}>
          <Typography id={titleId} variant="h5" fontWeight={600} lineHeight={1}>
            Карточка сотрудника
          </Typography>
          {error ? <Alert severity="error" action={onRetry ? <Button onClick={onRetry}>Повторить</Button> : undefined}>{error}</Alert>
            : !user ? <Stack direction="row" spacing={1} alignItems="center" role="status">
                <CircularProgress size={20} /><Typography>Загрузка карточки сотрудника…</Typography>
              </Stack>
              : <>
                  {headerActions}
                  <Box sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1,
                    p: { xs: 1.4, sm: 1.6 }, backgroundColor: 'background.paper' }}>
                    <Stack spacing={1.2}>
                      <SourceSection title="Сотрудник">
                        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 1.2 }}>
                          <InfoRow label="Логин" value={user.user_id} />
                          <Stack spacing={0.4} alignItems="flex-start">
                            <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                              Статус
                            </Typography>
                            <UserStatusPill value={user.status} />
                          </Stack>
                        </Box>
                      </SourceSection>
                      <SourceSection title="Профиль сотрудника">
                        <Stack spacing={1.2}>
                          <InfoRow label="ФИО" value={user.full_name} />
                          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 1.2 }}>
                            <InfoRow label="Телефон" value={formatPhoneForView(user.phone)} />
                            <InfoRow label="E-mail" value={<EmailWithVerifiedMark mail={user.mail}
                              verified={Boolean(user.email_verified)} showMark={showEmailVerification} />} />
                          </Box>
                        </Stack>
                      </SourceSection>
                    </Stack>
                  </Box>
                  <SourceSection title="Иерархия по объединениям">
                    <Stack spacing={1.2}>
                      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, minmax(0, 1fr))' }, gap: 1.2 }}>
                        <InfoRow label="Объединения" value={unitsCount} />
                        <InfoRow label="Руководители" value={managersCount} />
                        <InfoRow label="Подчинённые" value={subordinatesCount} />
                      </Box>
                      {isLoadingHierarchy ? <Typography variant="body2" color="text.secondary">Загружаем связи сотрудника...</Typography> : null}
                      {hierarchyError ? <Alert severity="warning"
                        action={onRetry ? <Button onClick={onRetry}>Повторить</Button> : undefined}>{hierarchyError}</Alert> : null}
                      {hierarchy ? <UserHierarchyTree hierarchy={hierarchy} unitsTree={unitsTree} /> : null}
                    </Stack>
                  </SourceSection>
                  {children}
                </>}
          <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="flex-end">
            <Button variant="outlined" onClick={onClose} sx={{ borderRadius: 1, textTransform: 'none' }}>Закрыть</Button>
          </Stack>
        </Stack>
      </DialogContent>
    </Dialog>
  );
};
