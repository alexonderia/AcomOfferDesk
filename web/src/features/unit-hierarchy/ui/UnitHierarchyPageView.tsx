import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined';
import ApartmentOutlinedIcon from '@mui/icons-material/ApartmentOutlined';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import GroupAddOutlinedIcon from '@mui/icons-material/GroupAddOutlined';
import PersonOutlineOutlinedIcon from '@mui/icons-material/PersonOutlineOutlined';
import PersonRemoveAlt1OutlinedIcon from '@mui/icons-material/PersonRemoveAlt1Outlined';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useMemo } from 'react';
import type { RecommendedHierarchyNode, UnitMember, UnitNode } from '@shared/api/units';
import { useUnitHierarchyPage } from '../model/useUnitHierarchyPage';

const statusLabelByCode: Record<string, string> = {
  active: 'Активен',
  inactive: 'Неактивен',
  review: 'На проверке',
  blacklist: 'Заблокирован',
};

const getUnitLevelLabel = (depth: number) => {
  if (depth === 0) {
    return 'Подразделение';
  }
  if (depth === 1) {
    return 'Проект';
  }
  return 'Модуль';
};

const getMemberAccentColor = (roleName: string) => {
  const normalizedRole = roleName.trim().toLowerCase();
  if (normalizedRole.includes('админ')) {
    return '#1d4ed8';
  }
  if (normalizedRole.includes('ведущ')) {
    return '#0f766e';
  }
  if (normalizedRole.includes('руковод')) {
    return '#7c3aed';
  }
  if (normalizedRole.includes('контраг')) {
    return '#b45309';
  }
  return '#475569';
};

const hierarchyConnectorColor = alpha('#0284c7', 0.72);
const recommendedCardWidth = 248;

const RecommendedNodeCard = ({
  node,
  depth,
}: {
  node: RecommendedHierarchyNode;
  depth: number;
}) => {
  const accent = getMemberAccentColor(node.role_name);
  const subordinateCount = node.children.length;

  return (
    <Card
      variant="outlined"
      sx={{
        width: recommendedCardWidth,
        minHeight: depth === 0 ? 168 : 150,
        borderRadius: 3,
        borderColor: alpha(accent, depth === 0 ? 0.26 : 0.18),
        background: `linear-gradient(180deg, ${alpha('#ffffff', 0.98)} 0%, ${alpha(accent, 0.06)} 100%)`,
        boxShadow: `0 12px 28px ${alpha('#0f172a', depth === 0 ? 0.09 : 0.05)}`,
        transition: 'border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease',
        '&:hover': {
          borderColor: alpha(accent, 0.34),
          boxShadow: `0 18px 36px ${alpha('#0f172a', 0.1)}`,
          transform: 'translateY(-1px)',
        },
      }}
    >
      <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Stack spacing={1.25} sx={{ height: '100%' }}>
          <Stack direction="row" spacing={1.1} alignItems="flex-start" minWidth={0}>
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: 2,
                display: 'grid',
                placeItems: 'center',
                bgcolor: alpha(accent, 0.12),
                color: accent,
                flexShrink: 0,
              }}
            >
              <PersonOutlineOutlinedIcon fontSize="small" />
            </Box>
            <Box minWidth={0} textAlign="left">
              <Typography fontWeight={700} sx={{ lineHeight: 1.2, overflowWrap: 'anywhere' }}>
                {node.full_name ?? node.user_id}
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.4, color: alpha('#0f172a', 0.78) }}>
                {node.role_name}
              </Typography>
            </Box>
          </Stack>

          <Box
            sx={{
              mt: 'auto',
              pt: 1.1,
              borderTop: `1px solid ${alpha('#cbd5e1', 0.85)}`,
            }}
          >
            <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap justifyContent="space-between">
              <Chip
                size="small"
                variant="outlined"
                label={statusLabelByCode[node.status] ?? node.status}
                sx={{ borderColor: alpha(accent, 0.2) }}
              />
              <Chip
                size="small"
                label={subordinateCount > 0 ? `Подчинённых: ${subordinateCount}` : 'Без подчинённых'}
                sx={{ bgcolor: alpha(accent, 0.12), color: accent }}
              />
            </Stack>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: 'block', mt: 0.9, textAlign: 'left', overflowWrap: 'anywhere' }}
            >
              {node.user_id}
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};

const RecommendedHierarchyChartItem = ({
  node,
  depth,
  isFirstChild,
  isLastChild,
  isOnlyChild,
}: {
  node: RecommendedHierarchyNode;
  depth: number;
  isFirstChild: boolean;
  isLastChild: boolean;
  isOnlyChild: boolean;
}) => {
  const connectorHeight = 24;

  const beforeConnector = {
    content: '""',
    position: 'absolute',
    top: 0,
    right: '50%',
    width: '50%',
    height: connectorHeight,
    borderTop: `1px solid ${hierarchyConnectorColor}`,
  } as const;

  const afterConnector = {
    content: '""',
    position: 'absolute',
    top: 0,
    left: '50%',
    width: '50%',
    height: connectorHeight,
    borderTop: `1px solid ${hierarchyConnectorColor}`,
    borderLeft: `1px solid ${hierarchyConnectorColor}`,
  } as const;

  return (
    <Box
      component="li"
      sx={[
        {
          position: 'relative',
          listStyle: 'none',
          px: { xs: 1, md: 1.5 },
          pt: depth === 0 ? 0 : 3,
          textAlign: 'center',
        },
        !isOnlyChild && {
          '&::before': beforeConnector,
          '&::after': afterConnector,
        },
        !isOnlyChild && isFirstChild && {
          '&::before': {
            display: 'none',
          },
          '&::after': {
            ...afterConnector,
            borderRadius: '12px 0 0 0',
          },
        },
        !isOnlyChild && isLastChild && {
          '&::after': {
            display: 'none',
          },
          '&::before': {
            ...beforeConnector,
            borderRight: `1px solid ${hierarchyConnectorColor}`,
            borderRadius: '0 12px 0 0',
          },
        },
      ]}
    >
      <RecommendedNodeCard node={node} depth={depth} />
      {node.children.length > 0 ? <RecommendedHierarchyChartList nodes={node.children} depth={depth + 1} /> : null}
    </Box>
  );
};

const RecommendedHierarchyChartList = ({
  nodes,
  depth = 0,
}: {
  nodes: RecommendedHierarchyNode[];
  depth?: number;
}) => (
  <Box
    component="ul"
    sx={{
      position: 'relative',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'flex-start',
      width: 'max-content',
      minWidth: '100%',
      m: 0,
      p: 0,
      pt: depth === 0 ? 0 : 3,
      listStyle: 'none',
      '&::before': depth === 0
        ? undefined
        : {
            content: '""',
            position: 'absolute',
            top: 0,
            left: '50%',
            width: 2,
            height: 24,
            bgcolor: hierarchyConnectorColor,
            transform: 'translateX(-50%)',
          },
    }}
  >
    {nodes.map((node, index) => (
      <RecommendedHierarchyChartItem
        key={node.user_id}
        node={node}
        depth={depth}
        isFirstChild={index === 0}
        isLastChild={index === nodes.length - 1}
        isOnlyChild={nodes.length === 1}
      />
    ))}
  </Box>
);

const MemberCard = ({
  unit,
  member,
  canManageMembers,
  onDeleteMember,
}: {
  unit: UnitNode;
  member: UnitMember;
  canManageMembers: boolean;
  onDeleteMember: (unit: UnitNode, member: UnitMember) => void;
}) => {
  const accent = getMemberAccentColor(member.role_name);

  return (
    <Box
      sx={{
        position: 'relative',
        borderRadius: 2,
        border: `1px solid ${alpha(accent, 0.22)}`,
        background: `linear-gradient(180deg, ${alpha(accent, 0.08)} 0%, rgba(255,255,255,0.98) 100%)`,
        p: 1.25,
        minWidth: 180,
      }}
    >
      <Stack spacing={0.75}>
        <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="flex-start">
          <Box minWidth={0}>
            <Typography fontWeight={700} sx={{ lineHeight: 1.15, overflowWrap: 'anywhere' }}>
              {member.full_name ?? member.user_id}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {member.user_id}
            </Typography>
          </Box>
          {canManageMembers ? (
            <Tooltip title="Удалить участника">
              <IconButton size="small" onClick={() => onDeleteMember(unit, member)}>
                <PersonRemoveAlt1OutlinedIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          ) : null}
        </Stack>
        <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap>
          <Chip size="small" label={member.role_name} sx={{ bgcolor: alpha(accent, 0.12), color: accent }} />
          <Chip size="small" variant="outlined" label={statusLabelByCode[member.status] ?? member.status} />
        </Stack>
      </Stack>
    </Box>
  );
};

const UnitNodeCard = ({
  unit,
  depth,
  onCreateChild,
  onRename,
  onDeactivate,
  onOpenMemberDialog,
  onDeleteMember,
}: {
  unit: UnitNode;
  depth: number;
  onCreateChild: (unit: UnitNode) => void;
  onRename: (unit: UnitNode) => void;
  onDeactivate: (unit: UnitNode) => void;
  onOpenMemberDialog: (unit: UnitNode) => void;
  onDeleteMember: (unit: UnitNode, member: UnitMember) => void;
}) => {
  const levelLabel = getUnitLevelLabel(depth);
  const canManageMembers = unit.actions.canManageMembers;

  return (
    <Box sx={{ position: 'relative', pl: depth === 0 ? 0 : { xs: 2, md: 3 } }}>
      {depth > 0 ? (
        <Box
          sx={{
            position: 'absolute',
            left: { xs: 8, md: 12 },
            top: 0,
            bottom: 0,
            width: 1,
            bgcolor: 'divider',
          }}
        />
      ) : null}
      <Card
        variant="outlined"
        sx={{
          position: 'relative',
          borderRadius: 3,
          borderColor: alpha('#2563eb', depth === 0 ? 0.28 : 0.14),
          boxShadow: `0 14px 34px ${alpha('#0f172a', 0.05)}`,
          overflow: 'visible',
        }}
      >
        <CardContent sx={{ p: { xs: 1.25, md: 1.5 }, '&:last-child': { pb: { xs: 1.25, md: 1.5 } } }}>
          <Stack spacing={1.5}>
            <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1.25}>
              <Stack direction="row" spacing={1.1} alignItems="center" minWidth={0}>
                <Box
                  sx={{
                    width: 42,
                    height: 42,
                    borderRadius: 2,
                    display: 'grid',
                    placeItems: 'center',
                    bgcolor: depth === 0 ? alpha('#2563eb', 0.12) : alpha('#0f766e', 0.1),
                    color: depth === 0 ? '#2563eb' : '#0f766e',
                    flexShrink: 0,
                  }}
                >
                  <ApartmentOutlinedIcon fontSize="small" />
                </Box>
                <Box minWidth={0}>
                  <Stack direction="row" spacing={0.75} alignItems="center" flexWrap="wrap" useFlexGap>
                    <Typography variant="h6" sx={{ fontSize: { xs: 18, md: 20 }, lineHeight: 1.15, overflowWrap: 'anywhere' }}>
                      {unit.name}
                    </Typography>
                    <Chip size="small" label={levelLabel} />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    {unit.members.length > 0 ? `Участников: ${unit.members.length}` : 'Пока без участников'}
                  </Typography>
                </Box>
              </Stack>

              <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                {unit.actions.canCreateChild ? (
                  <Tooltip title="Создать дочерний узел">
                    <IconButton size="small" onClick={() => onCreateChild(unit)}>
                      <AddOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                ) : null}
                {unit.actions.canUpdate ? (
                  <Tooltip title="Переименовать">
                    <IconButton size="small" onClick={() => onRename(unit)}>
                      <EditOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                ) : null}
                {unit.actions.canManageMembers ? (
                  <Tooltip title="Добавить участника">
                    <IconButton size="small" onClick={() => onOpenMemberDialog(unit)}>
                      <GroupAddOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                ) : null}
                {unit.actions.canDeactivate ? (
                  <Tooltip title="Деактивировать">
                    <IconButton size="small" color="error" onClick={() => onDeactivate(unit)}>
                      <DeleteOutlineRoundedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                ) : null}
              </Stack>
            </Stack>

            {unit.members.length > 0 ? (
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {unit.members.map((member) => (
                  <MemberCard
                    key={`${unit.unit_id}-${member.user_id}`}
                    unit={unit}
                    member={member}
                    canManageMembers={canManageMembers}
                    onDeleteMember={onDeleteMember}
                  />
                ))}
              </Stack>
            ) : (
              <Box
                sx={{
                  borderRadius: 2,
                  border: `1px dashed ${alpha('#94a3b8', 0.55)}`,
                  bgcolor: alpha('#f8fafc', 0.75),
                  px: 1.25,
                  py: 1,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  В этом узле пока нет закрепленных пользователей.
                </Typography>
              </Box>
            )}
          </Stack>
        </CardContent>
      </Card>

      {unit.children.length > 0 ? (
        <Stack spacing={1.5} sx={{ mt: 1.5 }}>
          {unit.children.map((child) => (
            <UnitNodeCard
              key={child.unit_id}
              unit={child}
              depth={depth + 1}
              onCreateChild={onCreateChild}
              onRename={onRename}
              onDeactivate={onDeactivate}
              onOpenMemberDialog={onOpenMemberDialog}
              onDeleteMember={onDeleteMember}
            />
          ))}
        </Stack>
      ) : null}
    </Box>
  );
};

export const UnitHierarchyPageView = () => {
  const {
    tree,
    recommendedTree,
    isLoading,
    error,
    recommendedError,
    canCreateRootUnit,
    unitDialogMode,
    activeUnit,
    unitName,
    setUnitName,
    isSavingUnit,
    isMemberDialogOpen,
    availableUsers,
    selectedUserId,
    setSelectedUserId,
    memberSearch,
    setMemberSearch,
    isLoadingUsers,
    isSavingMember,
    openCreateRootDialog,
    openCreateChildDialog,
    openRenameDialog,
    closeUnitDialog,
    submitUnit,
    deactivateUnit,
    openMemberDialog,
    closeMemberDialog,
    submitMember,
    deleteMember,
  } = useUnitHierarchyPage();

  const selectedUser = useMemo(
    () => availableUsers.find((user) => user.user_id === selectedUserId) ?? null,
    [availableUsers, selectedUserId]
  );

  return (
    <Stack spacing={2}>
      <Card
        sx={{
          borderRadius: 4,
          background: `linear-gradient(135deg, ${alpha('#2563eb', 0.08)} 0%, ${alpha('#0f766e', 0.06)} 100%)`,
          border: `1px solid ${alpha('#2563eb', 0.12)}`,
          boxShadow: `0 18px 40px ${alpha('#0f172a', 0.06)}`,
        }}
      >
        <CardContent sx={{ p: { xs: 1.5, md: 2 } }}>
          <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1.5}>
            <Box maxWidth={700}>
              <Typography variant="h4" sx={{ fontSize: { xs: 26, md: 32 }, lineHeight: 1.05, mb: 0.75 }}>
                Иерархия подразделений
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Управляйте подразделениями, проектами, модулями и закрепляйте действующих пользователей
                за нужными узлами без перезагрузки страницы.
              </Typography>
            </Box>
            {canCreateRootUnit ? (
              <Button variant="contained" startIcon={<AddOutlinedIcon />} onClick={openCreateRootDialog}>
                Создать подразделение
              </Button>
            ) : null}
          </Stack>
        </CardContent>
      </Card>

      {error ? <Alert severity="error">{error}</Alert> : null}

      <Card
        variant="outlined"
        sx={{
          borderRadius: 4,
          borderColor: alpha('#0f766e', 0.16),
          background: `linear-gradient(135deg, ${alpha('#0f766e', 0.05)} 0%, ${alpha('#2563eb', 0.03)} 100%)`,
        }}
      >
        <CardContent sx={{ p: { xs: 1.5, md: 2 } }}>
          <Stack spacing={1.5}>
            <Stack direction="row" spacing={1.1} alignItems="center">
              <Box
                sx={{
                  width: 42,
                  height: 42,
                  borderRadius: 2,
                  display: 'grid',
                  placeItems: 'center',
                  bgcolor: alpha('#0f766e', 0.12),
                  color: '#0f766e',
                  flexShrink: 0,
                }}
              >
                <AccountTreeOutlinedIcon fontSize="small" />
              </Box>
              <Box>
                <Typography variant="h6">Рекомендуемая структура</Typography>
                <Typography variant="body2" color="text.secondary">
                  Дерево строится по текущей управленческой иерархии пользователей и помогает вручную собирать реальные unit-узлы.
                </Typography>
              </Box>
            </Stack>

            {recommendedError ? <Alert severity="warning">{recommendedError}</Alert> : null}

            {recommendedTree.length === 0 && !recommendedError ? (
              <Alert severity="info">Для рекомендации пока не найдено активной иерархии пользователей.</Alert>
            ) : (
              <Box
                sx={{
                  overflowX: 'auto',
                  overflowY: 'hidden',
                  borderRadius: 3,
                  px: { xs: 0.5, md: 1 },
                  py: 1.5,
                  bgcolor: alpha('#dbeafe', 0.28),
                  border: `1px solid ${alpha('#7dd3fc', 0.24)}`,
                }}
              >
                <Box sx={{ width: 'max-content', minWidth: '100%', mx: 'auto' }}>
                  <RecommendedHierarchyChartList nodes={recommendedTree} />
                </Box>
              </Box>
            )}
          </Stack>
        </CardContent>
      </Card>

      {isLoading ? (
        <Box sx={{ display: 'grid', placeItems: 'center', minHeight: 240 }}>
          <CircularProgress />
        </Box>
      ) : tree.length === 0 ? (
        <Alert severity="info">Пока не создано ни одного подразделения.</Alert>
      ) : (
        <Stack spacing={2}>
          {tree.map((unit) => (
            <UnitNodeCard
              key={unit.unit_id}
              unit={unit}
              depth={0}
              onCreateChild={openCreateChildDialog}
              onRename={openRenameDialog}
              onDeactivate={deactivateUnit}
              onOpenMemberDialog={openMemberDialog}
              onDeleteMember={deleteMember}
            />
          ))}
        </Stack>
      )}

      <Dialog open={unitDialogMode !== null} onClose={closeUnitDialog} maxWidth="xs" fullWidth>
        <DialogTitle>
          {unitDialogMode === 'rename'
            ? 'Переименование подразделения'
            : unitDialogMode === 'create-child'
              ? 'Создать дочерний узел'
              : 'Создать подразделение'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={1.25} sx={{ pt: 0.5 }}>
            {activeUnit && unitDialogMode === 'create-child' ? (
              <Alert severity="info">Новый узел будет создан внутри «{activeUnit.name}».</Alert>
            ) : null}
            <TextField
              autoFocus
              label="Название"
              value={unitName}
              onChange={(event) => setUnitName(event.target.value)}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeUnitDialog}>Отмена</Button>
          <Button onClick={submitUnit} variant="contained" disabled={isSavingUnit}>
            {isSavingUnit ? 'Сохранение...' : 'Сохранить'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={isMemberDialogOpen} onClose={closeMemberDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Добавить участника</DialogTitle>
        <DialogContent>
          <Stack spacing={1.25} sx={{ pt: 0.5 }}>
            {activeUnit ? (
              <Alert severity="info">Подразделение: «{activeUnit.name}»</Alert>
            ) : null}
            <Autocomplete
              options={availableUsers}
              loading={isLoadingUsers}
              value={selectedUser}
              onChange={(_event, value) => setSelectedUserId(value?.user_id ?? '')}
              inputValue={memberSearch}
              onInputChange={(_event, value) => setMemberSearch(value)}
              getOptionLabel={(option) => option.full_name ? `${option.full_name} (${option.user_id})` : option.user_id}
              isOptionEqualToValue={(option, value) => option.user_id === value.user_id}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Пользователь"
                  placeholder="Начните вводить имя или логин"
                />
              )}
              renderOption={(props, option) => (
                <Box component="li" {...props}>
                  <Stack spacing={0.25}>
                    <Typography>{option.full_name ?? option.user_id}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {option.role_name} • {option.user_id}
                    </Typography>
                  </Stack>
                </Box>
              )}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeMemberDialog}>Отмена</Button>
          <Button onClick={submitMember} variant="contained" disabled={isSavingMember || !selectedUserId}>
            {isSavingMember ? 'Добавление...' : 'Добавить'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};
