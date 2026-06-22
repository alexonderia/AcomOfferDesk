import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined';
import ApartmentOutlinedIcon from '@mui/icons-material/ApartmentOutlined';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import GroupAddOutlinedIcon from '@mui/icons-material/GroupAddOutlined';
import Groups2OutlinedIcon from '@mui/icons-material/Groups2Outlined';
import HubOutlinedIcon from '@mui/icons-material/HubOutlined';
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

const hierarchyPageColors = {
  canvas: '#eef1f9',
  canvasBorder: '#d4d9e6',
  cardBorder: '#cfd6e3',
  connector: '#3a9cc7',
  shadow: '0 4px 12px rgba(27, 39, 57, 0.08)',
  textPrimary: '#172033',
  textSecondary: '#7a8699',
  softBlue: '#3f83f8',
  softPink: '#d36b97',
  softTeal: '#50a4a2',
};

const hierarchyConnectorColor = hierarchyPageColors.connector;
const recommendedCardWidth = 162;
const recommendedRootCardWidth = 176;

const sectionCardSx = {
  borderRadius: 4,
  borderColor: hierarchyPageColors.canvasBorder,
  background: alpha('#ffffff', 0.72),
  boxShadow: '0 1px 0 rgba(255, 255, 255, 0.7) inset',
};

const isRecommendationPlaceholder = (node: RecommendedHierarchyNode) => {
  const fullName = (node.full_name ?? '').trim().toLowerCase();
  return fullName.includes('вакан') || fullName.includes('не указано');
};

const getRecommendedDescendantCount = (node: RecommendedHierarchyNode): number =>
  node.children.reduce((total, child) => total + 1 + getRecommendedDescendantCount(child), 0);

const RecommendedNodeCard = ({
  node,
  depth,
}: {
  node: RecommendedHierarchyNode;
  depth: number;
}) => {
  const subordinateCount = node.children.length;
  const descendantCount = getRecommendedDescendantCount(node);
  const cardWidth = depth === 0 ? recommendedRootCardWidth : recommendedCardWidth;
  const isPlaceholder = isRecommendationPlaceholder(node);
  const borderColor = isPlaceholder ? alpha(hierarchyPageColors.softPink, 0.55) : hierarchyPageColors.cardBorder;
  const helperLabel = depth === 0 ? 'Модуль 2' : null;

  return (
    <Card
      variant="outlined"
      sx={{
        width: cardWidth,
        minHeight: depth === 0 ? 136 : 100,
        borderRadius: 1.8,
        borderColor,
        backgroundColor: '#ffffff',
        boxShadow: '0 2px 8px rgba(27, 39, 57, 0.08)',
        transition: 'border-color 160ms ease, box-shadow 160ms ease',
        '&:hover': {
          borderColor: isPlaceholder ? alpha(hierarchyPageColors.softPink, 0.72) : alpha(hierarchyPageColors.connector, 0.42),
          boxShadow: '0 4px 12px rgba(27, 39, 57, 0.1)',
        },
      }}
    >
      <CardContent sx={{ p: 1.05, '&:last-child': { pb: 1.05 } }}>
        <Stack spacing={0.8} sx={{ height: '100%' }}>
          <Box minWidth={0} textAlign="left">
            <Typography
              fontWeight={600}
              sx={{
                color: isPlaceholder ? hierarchyPageColors.softPink : hierarchyPageColors.textPrimary,
                fontSize: 11.3,
                lineHeight: 1.22,
                overflowWrap: 'anywhere',
              }}
            >
              {node.full_name ?? node.user_id}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                mt: 0.25,
                color: hierarchyPageColors.textPrimary,
                fontSize: 10.35,
                lineHeight: 1.2,
              }}
            >
              {node.role_name}
            </Typography>
            {helperLabel ? (
              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  mt: 0.9,
                  color: alpha(hierarchyPageColors.textSecondary, 0.82),
                  fontSize: 9.9,
                }}
              >
                {helperLabel}
              </Typography>
            ) : null}
          </Box>

          <Box sx={{ mt: 'auto', pt: depth === 0 ? 0.7 : 0.45 }}>
            <Stack direction="row" spacing={0.75} justifyContent="flex-end" alignItems="center">
              <Tooltip title={`Всего подчинённых: ${descendantCount}`}>
                <Stack direction="row" spacing={0.15} alignItems="center" sx={{ color: hierarchyPageColors.softBlue }}>
                  <Typography variant="caption" sx={{ fontSize: 10.4, fontWeight: 700 }}>
                    {descendantCount}
                  </Typography>
                  <Groups2OutlinedIcon sx={{ fontSize: 11.5 }} />
                </Stack>
              </Tooltip>
              <Tooltip title={`Прямых подчинённых: ${subordinateCount}`}>
                <Stack direction="row" spacing={0.15} alignItems="center" sx={{ color: hierarchyPageColors.softPink }}>
                  <Typography variant="caption" sx={{ fontSize: 10.4, fontWeight: 700 }}>
                    {subordinateCount}
                  </Typography>
                  <PersonOutlineOutlinedIcon sx={{ fontSize: 11.5 }} />
                </Stack>
              </Tooltip>
              <Tooltip title={`Уровень в дереве: ${depth + 1}`}>
                <Stack direction="row" spacing={0.15} alignItems="center" sx={{ color: alpha('#7c3aed', 0.8) }}>
                  <Typography variant="caption" sx={{ fontSize: 10.4, fontWeight: 700 }}>
                    {depth + 1}
                  </Typography>
                  <HubOutlinedIcon sx={{ fontSize: 11.5 }} />
                </Stack>
              </Tooltip>
            </Stack>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};

const connectorLineSx = {
  backgroundColor: hierarchyConnectorColor,
  borderRadius: 999,
} as const;

const RecommendedHierarchyTreeNode = ({
  node,
  depth,
}: {
  node: RecommendedHierarchyNode;
  depth: number;
}) => {
  const hasChildren = node.children.length > 0;
  const hasMultipleChildren = node.children.length > 1;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 'max-content' }}>
      <RecommendedNodeCard node={node} depth={depth} />

      {hasChildren ? (
        <Box sx={{ mt: 0.9, display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
          <Box sx={{ ...connectorLineSx, width: '1px', height: '18px' }} />

          {hasMultipleChildren ? (
            <Box sx={{ position: 'relative', pt: 2.1 }}>
              <Box
                sx={{
                  ...connectorLineSx,
                  position: 'absolute',
                  top: 0,
                  left: `calc(${50 / node.children.length}% )`,
                  right: `calc(${50 / node.children.length}% )`,
                  height: '1px',
                }}
              />
              <Stack direction="row" spacing={1.2} alignItems="flex-start">
                {node.children.map((child) => (
                  <Box key={child.user_id} sx={{ position: 'relative', pt: 2.1 }}>
                    <Box
                      sx={{
                        ...connectorLineSx,
                        position: 'absolute',
                        top: 0,
                        left: '50%',
                        width: '1px',
                        height: '14px',
                        transform: 'translateX(-50%)',
                      }}
                    />
                    <RecommendedHierarchyTreeNode node={child} depth={depth + 1} />
                  </Box>
                ))}
              </Stack>
            </Box>
          ) : (
            <RecommendedHierarchyTreeNode node={node.children[0]!} depth={depth + 1} />
          )}
        </Box>
      ) : null}
    </Box>
  );
};

const RecommendedHierarchyForest = ({
  nodes,
}: {
  nodes: RecommendedHierarchyNode[];
}) => (
  <Stack spacing={5} alignItems="center">
    {nodes.map((node) => (
      <Box key={node.user_id} sx={{ width: 'max-content', minWidth: '100%' }}>
        <RecommendedHierarchyTreeNode node={node} depth={0} />
      </Box>
    ))}
  </Stack>
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
        border: `1px solid ${alpha(hierarchyPageColors.cardBorder, 0.95)}`,
        backgroundColor: '#ffffff',
        boxShadow: '0 2px 8px rgba(27, 39, 57, 0.05)',
        p: 1.15,
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
          <Chip size="small" label={member.role_name} sx={{ bgcolor: alpha(accent, 0.1), color: accent }} />
          <Chip
            size="small"
            variant="outlined"
            label={statusLabelByCode[member.status] ?? member.status}
            sx={{ borderColor: alpha(hierarchyPageColors.cardBorder, 0.95) }}
          />
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
            width: '1px',
            bgcolor: alpha(hierarchyPageColors.connector, 0.55),
          }}
        />
      ) : null}
      <Card
        variant="outlined"
        sx={{
          position: 'relative',
          borderRadius: 3,
          borderColor: hierarchyPageColors.cardBorder,
          backgroundColor: alpha('#ffffff', 0.94),
          boxShadow: '0 4px 14px rgba(27, 39, 57, 0.06)',
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
                    bgcolor: depth === 0 ? alpha(hierarchyPageColors.softBlue, 0.1) : alpha(hierarchyPageColors.softTeal, 0.12),
                    color: depth === 0 ? hierarchyPageColors.softBlue : hierarchyPageColors.softTeal,
                    flexShrink: 0,
                  }}
                >
                  <ApartmentOutlinedIcon fontSize="small" />
                </Box>
                <Box minWidth={0}>
                  <Stack direction="row" spacing={0.75} alignItems="center" flexWrap="wrap" useFlexGap>
                    <Typography
                      variant="h6"
                      sx={{
                        fontSize: { xs: 17, md: 19 },
                        lineHeight: 1.15,
                        overflowWrap: 'anywhere',
                        color: hierarchyPageColors.textPrimary,
                      }}
                    >
                      {unit.name}
                    </Typography>
                    <Chip
                      size="small"
                      label={levelLabel}
                      sx={{
                        bgcolor: alpha('#ffffff', 0.9),
                        border: `1px solid ${alpha(hierarchyPageColors.cardBorder, 0.95)}`,
                      }}
                    />
                  </Stack>
                  <Typography variant="body2" sx={{ color: hierarchyPageColors.textSecondary }}>
                    {unit.members.length > 0 ? `Участников: ${unit.members.length}` : 'Пока без участников'}
                  </Typography>
                </Box>
              </Stack>

              <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                {unit.actions.canCreateChild ? (
                  <Tooltip title="Создать дочерний узел">
                    <IconButton
                      size="small"
                      onClick={() => onCreateChild(unit)}
                      sx={{ border: `1px solid ${alpha(hierarchyPageColors.cardBorder, 0.95)}` }}
                    >
                      <AddOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                ) : null}
                {unit.actions.canUpdate ? (
                  <Tooltip title="Переименовать">
                    <IconButton
                      size="small"
                      onClick={() => onRename(unit)}
                      sx={{ border: `1px solid ${alpha(hierarchyPageColors.cardBorder, 0.95)}` }}
                    >
                      <EditOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                ) : null}
                {unit.actions.canManageMembers ? (
                  <Tooltip title="Добавить участника">
                    <IconButton
                      size="small"
                      onClick={() => onOpenMemberDialog(unit)}
                      sx={{ border: `1px solid ${alpha(hierarchyPageColors.cardBorder, 0.95)}` }}
                    >
                      <GroupAddOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                ) : null}
                {unit.actions.canDeactivate ? (
                  <Tooltip title="Деактивировать">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => onDeactivate(unit)}
                      sx={{ border: `1px solid ${alpha('#f0b6c8', 0.95)}` }}
                    >
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
                  border: `1px dashed ${alpha(hierarchyPageColors.canvasBorder, 0.9)}`,
                  bgcolor: alpha('#ffffff', 0.76),
                  px: 1.25,
                  py: 1,
                }}
              >
                <Typography variant="body2" sx={{ color: hierarchyPageColors.textSecondary }}>
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
    <Box
      sx={{
        borderRadius: { xs: 4, md: 5 },
        bgcolor: hierarchyPageColors.canvas,
        border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.92)}`,
        px: { xs: 1.25, md: 2.25 },
        py: { xs: 1.5, md: 2.5 },
      }}
    >
      <Stack spacing={2.25}>
        <Card variant="outlined" sx={sectionCardSx}>
          <CardContent sx={{ p: { xs: 1.5, md: 2 } }}>
            <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1.5}>
              <Box maxWidth={720}>
                <Typography
                  variant="overline"
                  sx={{ color: hierarchyPageColors.softBlue, letterSpacing: 1.4, fontWeight: 700 }}
                >
                  Страница иерархии
                </Typography>
                <Typography
                  variant="h4"
                  sx={{
                    fontSize: { xs: 24, md: 29 },
                    lineHeight: 1.08,
                    mt: 0.35,
                    mb: 0.75,
                    color: hierarchyPageColors.textPrimary,
                  }}
                >
                  Иерархия подразделений
                </Typography>
                <Typography variant="body1" sx={{ color: hierarchyPageColors.textSecondary }}>
                  Светлая схема помогает быстро сопоставить рекомендуемую структуру из текущей иерархии пользователей
                  и рабочее дерево реальных unit-узлов.
                </Typography>
              </Box>
              {canCreateRootUnit ? (
                <Button
                  variant="contained"
                  startIcon={<AddOutlinedIcon />}
                  onClick={openCreateRootDialog}
                  sx={{
                    alignSelf: { xs: 'stretch', md: 'flex-start' },
                    bgcolor: hierarchyPageColors.softBlue,
                    boxShadow: 'none',
                    '&:hover': {
                      bgcolor: '#2f72e3',
                      boxShadow: 'none',
                    },
                  }}
                >
                  Создать подразделение
                </Button>
              ) : null}
            </Stack>
          </CardContent>
        </Card>

        {error ? <Alert severity="error">{error}</Alert> : null}

        <Card variant="outlined" sx={sectionCardSx}>
          <CardContent sx={{ p: { xs: 1.5, md: 2 } }}>
            <Stack spacing={1.5}>
              <Stack direction="row" spacing={1.1} alignItems="center">
                <Box
                  sx={{
                    width: 38,
                    height: 38,
                    borderRadius: 2,
                    display: 'grid',
                    placeItems: 'center',
                    bgcolor: alpha(hierarchyPageColors.softBlue, 0.12),
                    color: hierarchyPageColors.softBlue,
                    flexShrink: 0,
                  }}
                >
                  <AccountTreeOutlinedIcon fontSize="small" />
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ color: hierarchyPageColors.textPrimary }}>
                    Рекомендуемая структура
                  </Typography>
                  <Typography variant="body2" sx={{ color: hierarchyPageColors.textSecondary }}>
                    Визуальный ориентир на основе текущей иерархии пользователей, оформленный в стиле оргсхемы из референса.
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
                    px: { xs: 1, md: 1.5 },
                    py: { xs: 1.5, md: 2 },
                    bgcolor: hierarchyPageColors.canvas,
                    border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
                  }}
                >
                  <Box sx={{ width: 'max-content', minWidth: '100%', mx: 'auto' }}>
                    <RecommendedHierarchyForest nodes={recommendedTree} />
                  </Box>
                </Box>
              )}
            </Stack>
          </CardContent>
        </Card>

        <Card variant="outlined" sx={sectionCardSx}>
          <CardContent sx={{ p: { xs: 1.5, md: 2 } }}>
            <Stack spacing={1.5}>
              <Stack direction="row" spacing={1.1} alignItems="center">
                <Box
                  sx={{
                    width: 38,
                    height: 38,
                    borderRadius: 2,
                    display: 'grid',
                    placeItems: 'center',
                    bgcolor: alpha(hierarchyPageColors.softTeal, 0.12),
                    color: hierarchyPageColors.softTeal,
                    flexShrink: 0,
                  }}
                >
                  <ApartmentOutlinedIcon fontSize="small" />
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ color: hierarchyPageColors.textPrimary }}>
                    Рабочая структура
                  </Typography>
                  <Typography variant="body2" sx={{ color: hierarchyPageColors.textSecondary }}>
                    Здесь создаются и редактируются реальные подразделения, проекты, модули и привязки пользователей.
                  </Typography>
                </Box>
              </Stack>

              {isLoading ? (
                <Box sx={{ display: 'grid', placeItems: 'center', minHeight: 240 }}>
                  <CircularProgress />
                </Box>
              ) : tree.length === 0 ? (
                <Alert severity="info">Пока не создано ни одного подразделения.</Alert>
              ) : (
                <Box
                  sx={{
                    borderRadius: 3.5,
                    bgcolor: hierarchyPageColors.canvas,
                    border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
                    p: { xs: 1.25, md: 1.75 },
                  }}
                >
                  <Stack spacing={1.5}>
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
                </Box>
              )}
            </Stack>
          </CardContent>
        </Card>

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
    </Box>
  );
};
