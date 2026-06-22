import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined';
import ApartmentOutlinedIcon from '@mui/icons-material/ApartmentOutlined';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import GroupAddOutlinedIcon from '@mui/icons-material/GroupAddOutlined';
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
const recommendedCardWidth = 196;
const recommendedRootCardWidth = 206;

const sectionCardSx = {
  borderRadius: 4,
  borderColor: hierarchyPageColors.canvasBorder,
  background: alpha('#ffffff', 0.72),
  boxShadow: '0 1px 0 rgba(255, 255, 255, 0.7) inset',
};

const RecommendedNodeCard = ({
  node,
  depth,
}: {
  node: RecommendedHierarchyNode;
  depth: number;
}) => {
  const subordinateCount = node.children.length;
  const cardWidth = depth === 0 ? recommendedRootCardWidth : recommendedCardWidth;
  const statusAccent = node.status === 'active' ? hierarchyPageColors.softPink : hierarchyPageColors.textSecondary;

  return (
    <Card
      variant="outlined"
      sx={{
        width: cardWidth,
        minHeight: depth === 0 ? 136 : 116,
        borderRadius: 2,
        borderColor: hierarchyPageColors.cardBorder,
        backgroundColor: '#ffffff',
        boxShadow: hierarchyPageColors.shadow,
        transition: 'border-color 160ms ease, box-shadow 160ms ease',
        '&:hover': {
          borderColor: alpha(hierarchyPageColors.connector, 0.4),
          boxShadow: '0 6px 16px rgba(27, 39, 57, 0.11)',
        },
      }}
    >
      <CardContent sx={{ p: 1.35, '&:last-child': { pb: 1.35 } }}>
        <Stack spacing={1.25} sx={{ height: '100%' }}>
          <Box minWidth={0} textAlign="left">
            <Typography
              fontWeight={600}
              sx={{
                color: hierarchyPageColors.textPrimary,
                fontSize: 14,
                lineHeight: 1.25,
                overflowWrap: 'anywhere',
              }}
            >
              {node.full_name ?? node.user_id}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                mt: 0.45,
                color: hierarchyPageColors.textPrimary,
                fontSize: 12.5,
                lineHeight: 1.25,
              }}
            >
              {node.role_name}
            </Typography>
            <Typography
              variant="caption"
              sx={{
                display: 'block',
                mt: 1.1,
                color: hierarchyPageColors.textSecondary,
                fontSize: 11.5,
              }}
            >
              {depth === 0 ? 'Корневой узел' : `Уровень ${depth + 1}`}
            </Typography>
          </Box>

          <Box
            sx={{
              mt: 'auto',
              pt: 0.85,
            }}
          >
            <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="center">
              <Typography
                variant="caption"
                sx={{
                  color: hierarchyPageColors.textSecondary,
                  fontSize: 11.5,
                  overflowWrap: 'anywhere',
                }}
              >
                {node.user_id}
              </Typography>
              <Stack direction="row" spacing={1.1} alignItems="center">
                <Stack direction="row" spacing={0.4} alignItems="center">
                  <Typography variant="caption" sx={{ color: hierarchyPageColors.softBlue, fontWeight: 700 }}>
                    {subordinateCount}
                  </Typography>
                  <Box
                    sx={{
                      width: 7,
                      height: 7,
                      borderRadius: '50%',
                      bgcolor: hierarchyPageColors.softBlue,
                    }}
                  />
                </Stack>
                <Stack direction="row" spacing={0.4} alignItems="center">
                  <Typography variant="caption" sx={{ color: statusAccent, fontWeight: 700 }}>
                    1
                  </Typography>
                  <Box
                    sx={{
                      width: 7,
                      height: 7,
                      borderRadius: '50%',
                      bgcolor: statusAccent,
                    }}
                  />
                </Stack>
              </Stack>
            </Stack>
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
  const connectorHeight = 26;

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
          px: { xs: 1, md: 1.35 },
          pt: depth === 0 ? 0 : 3.25,
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
      pt: depth === 0 ? 0 : 3.25,
      listStyle: 'none',
      '&::before': depth === 0
        ? undefined
        : {
            content: '""',
            position: 'absolute',
            top: 0,
            left: '50%',
            width: 1,
            height: 26,
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
            width: 1,
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
                    borderRadius: 3.5,
                    px: { xs: 1.25, md: 2 },
                    py: { xs: 2, md: 2.5 },
                    bgcolor: hierarchyPageColors.canvas,
                    border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
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
