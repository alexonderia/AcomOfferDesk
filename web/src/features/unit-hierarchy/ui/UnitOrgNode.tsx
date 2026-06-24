import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import GroupAddOutlinedIcon from '@mui/icons-material/GroupAddOutlined';
import MoreHorizOutlinedIcon from '@mui/icons-material/MoreHorizOutlined';
import {
  Box,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Stack,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useState } from 'react';
import type { UnitNode } from '@shared/api/units';
import {
  connectorLineSx,
  getUnitLevelLabel,
  hierarchyPageColors,
  hierarchySurfaceBackground,
} from './unitHierarchyStyles';

type UnitOrgNodeProps = {
  depth: number;
  onCreateChild?: ((unit: UnitNode) => void) | undefined;
  onDeactivate: (unit: UnitNode) => void;
  onOpenMemberDialog?: ((unit: UnitNode) => void) | undefined;
  onOpenUnitDetails?: ((unit: UnitNode) => void) | undefined;
  onRename: (unit: UnitNode) => void;
  showMembers?: boolean;
  showPrimaryActions?: boolean;
  unit: UnitNode;
};

const getCreateChildActionLabel = () => 'Добавить дочерний юнит';

export const UnitOrgNode = ({
  depth,
  onCreateChild,
  onDeactivate,
  onOpenMemberDialog,
  onOpenUnitDetails,
  onRename,
  showMembers = true,
  showPrimaryActions = true,
  unit,
}: UnitOrgNodeProps) => {
  const [menuAnchorEl, setMenuAnchorEl] = useState<HTMLElement | null>(null);
  const hasMenuActions = unit.actions.canUpdate || unit.actions.canDeactivate;
  const hasVisiblePrimaryActions = showPrimaryActions && (
    (unit.actions.canCreateChild && Boolean(onCreateChild))
    || (unit.actions.canManageMembers && Boolean(onOpenMemberDialog))
  );
  const canCreateChild = unit.actions.canCreateChild && Boolean(onCreateChild);
  const canOpenMemberDialog = unit.actions.canManageMembers && Boolean(onOpenMemberDialog);
  const canOpenUnitDetails = Boolean(onOpenUnitDetails);

  const openUnitDetails = () => {
    onOpenUnitDetails?.(unit);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 'max-content' }}>
      <Stack spacing={1.25} alignItems="center" sx={{ width: 'max-content' }}>
        <Box
          role={canOpenUnitDetails ? 'button' : undefined}
          aria-label={canOpenUnitDetails ? `Открыть состав юнита ${unit.name}` : undefined}
          tabIndex={canOpenUnitDetails ? 0 : undefined}
          onClick={canOpenUnitDetails ? openUnitDetails : undefined}
          onKeyDown={canOpenUnitDetails
            ? (event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                openUnitDetails();
              }
            }
            : undefined}
          sx={{
            width: 332,
            maxWidth: 'min(332px, calc(100vw - 40px))',
            borderRadius: 3,
            border: `1px solid ${alpha(hierarchyPageColors.cardBorder, 0.98)}`,
            backgroundImage: hierarchySurfaceBackground,
            backgroundColor: alpha('#ffffff', 0.96),
            boxShadow: hierarchyPageColors.shadow,
            px: 1.4,
            py: 1.3,
            zIndex: 1,
            cursor: canOpenUnitDetails ? 'pointer' : 'default',
          }}
        >
          <Stack spacing={1.15}>
            <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="flex-start">
              <Box sx={{ minWidth: 0 }}>
                <Typography
                  variant="caption"
                  sx={{
                    display: 'block',
                    color: alpha(hierarchyPageColors.textSecondary, 0.9),
                    fontSize: 10.5,
                    fontWeight: 700,
                    letterSpacing: 0.35,
                    textTransform: 'uppercase',
                  }}
                >
                  {getUnitLevelLabel(depth)}
                </Typography>
                <Typography
                  sx={{
                    mt: 0.35,
                    color: hierarchyPageColors.textPrimary,
                    fontSize: 15,
                    fontWeight: 700,
                    lineHeight: 1.24,
                    overflowWrap: 'anywhere',
                  }}
                >
                  {unit.name}
                </Typography>
              </Box>

              {hasMenuActions ? (
                <>
                  <IconButton
                    size="small"
                    onClick={(event) => {
                      event.stopPropagation();
                      setMenuAnchorEl(event.currentTarget);
                    }}
                    sx={{
                      mt: -0.2,
                      mr: -0.35,
                      color: alpha(hierarchyPageColors.textSecondary, 0.92),
                    }}
                  >
                    <MoreHorizOutlinedIcon sx={{ fontSize: 18 }} />
                  </IconButton>
                  <Menu anchorEl={menuAnchorEl} open={Boolean(menuAnchorEl)} onClose={() => setMenuAnchorEl(null)}>
                    {unit.actions.canUpdate ? (
                      <MenuItem
                        onClick={() => {
                          setMenuAnchorEl(null);
                          onRename(unit);
                        }}
                      >
                        <EditOutlinedIcon sx={{ mr: 1, fontSize: 18 }} />
                        Переименовать юнит
                      </MenuItem>
                    ) : null}
                    {unit.actions.canDeactivate ? (
                      <MenuItem
                        onClick={() => {
                          setMenuAnchorEl(null);
                          onDeactivate(unit);
                        }}
                        sx={{ color: 'error.main' }}
                      >
                        <DeleteOutlineRoundedIcon sx={{ mr: 1, fontSize: 18 }} />
                        Деактивировать юнит
                      </MenuItem>
                    ) : null}
                  </Menu>
                </>
              ) : null}
            </Stack>

            <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
              <Box
                sx={{
                  borderRadius: 999,
                  px: 1,
                  py: 0.38,
                  backgroundColor: alpha(hierarchyPageColors.softBlue, 0.08),
                  color: hierarchyPageColors.softBlue,
                  fontSize: 11.5,
                  fontWeight: 700,
                  lineHeight: 1.2,
                }}
              >
                Участники: {unit.members.length}
              </Box>
              <Box
                sx={{
                  borderRadius: 999,
                  px: 1,
                  py: 0.38,
                  backgroundColor: alpha(hierarchyPageColors.softTeal, 0.08),
                  color: hierarchyPageColors.softTeal,
                  fontSize: 11.5,
                  fontWeight: 700,
                  lineHeight: 1.2,
                }}
              >
                Вложенные юниты: {unit.children.length}
              </Box>
            </Stack>

            {hasVisiblePrimaryActions ? (
              <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                {canCreateChild ? (
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<AddOutlinedIcon sx={{ fontSize: 16 }} />}
                    onClick={(event) => {
                      event.stopPropagation();
                      onCreateChild?.(unit);
                    }}
                    sx={{ minHeight: 30, px: 1.15, py: 0.25, borderRadius: 1.4, textTransform: 'none' }}
                  >
                    {getCreateChildActionLabel()}
                  </Button>
                ) : null}
                {canOpenMemberDialog ? (
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<GroupAddOutlinedIcon sx={{ fontSize: 16 }} />}
                    onClick={(event) => {
                      event.stopPropagation();
                      onOpenMemberDialog?.(unit);
                    }}
                    sx={{ minHeight: 30, px: 1.15, py: 0.25, borderRadius: 1.4, textTransform: 'none' }}
                  >
                    Добавить сотрудника
                  </Button>
                ) : null}
              </Stack>
            ) : null}

            {canOpenUnitDetails ? (
              <Box
                sx={{
                  borderRadius: 2,
                  border: '1px solid',
                  borderColor: alpha(hierarchyPageColors.canvasBorder, 0.95),
                  backgroundColor: alpha(hierarchyPageColors.canvas, 0.72),
                  p: 1,
                }}
              >
                <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="center">
                  <Box sx={{ minWidth: 0 }}>
                    <Typography sx={{ color: hierarchyPageColors.textPrimary, fontSize: 13.5, fontWeight: 700 }}>
                      {showMembers ? 'Состав юнита' : 'Участники юнита'}
                    </Typography>
                    <Typography variant="caption" sx={{ color: hierarchyPageColors.textSecondary }}>
                      Нажмите на карточку, чтобы открыть список участников
                    </Typography>
                  </Box>
                  <Button
                    size="small"
                    variant="text"
                    onClick={(event) => {
                      event.stopPropagation();
                      openUnitDetails();
                    }}
                    sx={{ flexShrink: 0, textTransform: 'none' }}
                  >
                    Открыть
                  </Button>
                </Stack>
              </Box>
            ) : null}

            {unit.children.length === 0 ? (
              <Box
                sx={{
                  borderRadius: 2,
                  border: `1px dashed ${alpha(hierarchyPageColors.softTeal, 0.34)}`,
                  backgroundColor: alpha(hierarchyPageColors.softTeal, 0.04),
                  px: 1.1,
                  py: 0.95,
                }}
              >
                <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="center">
                  <Box sx={{ minWidth: 0 }}>
                    <Typography sx={{ color: hierarchyPageColors.textPrimary, fontSize: 13, fontWeight: 700 }}>
                      Место для нового юнита
                    </Typography>
                    <Typography variant="caption" sx={{ color: hierarchyPageColors.textSecondary }}>
                      В эту ветку можно добавить дочерний юнит
                    </Typography>
                  </Box>
                  {canCreateChild ? (
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<AddOutlinedIcon sx={{ fontSize: 16 }} />}
                      onClick={(event) => {
                        event.stopPropagation();
                        onCreateChild?.(unit);
                      }}
                      sx={{ flexShrink: 0, textTransform: 'none' }}
                    >
                      Создать
                    </Button>
                  ) : null}
                </Stack>
              </Box>
            ) : null}
          </Stack>
        </Box>
      </Stack>

      {unit.children.length > 0 ? (
        <Box sx={{ mt: 2.2, display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
          <Box sx={{ ...connectorLineSx, width: '1px', height: '20px' }} />

          <Box sx={{ display: 'flex', gap: 2.2, alignItems: 'flex-start', justifyContent: 'center', width: 'max-content' }}>
            {unit.children.map((child, index) => {
              const isFirst = index === 0;
              const isLast = index === unit.children.length - 1;
              const hasManyChildren = unit.children.length > 1;

              return (
                <Box key={child.unit_id} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 'max-content' }}>
                  {hasManyChildren ? (
                    <Box sx={{ position: 'relative', width: '100%', height: '20px', minWidth: 220 }}>
                      {!isFirst ? (
                        <Box
                          sx={{
                            ...connectorLineSx,
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: '50%',
                            height: '1px',
                          }}
                        />
                      ) : null}
                      {!isLast ? (
                        <Box
                          sx={{
                            ...connectorLineSx,
                            position: 'absolute',
                            top: 0,
                            left: '50%',
                            right: 0,
                            height: '1px',
                          }}
                        />
                      ) : null}
                      <Box
                        sx={{
                          ...connectorLineSx,
                          position: 'absolute',
                          top: 0,
                          left: '50%',
                          width: '1px',
                          height: '20px',
                          transform: 'translateX(-50%)',
                        }}
                      />
                    </Box>
                  ) : (
                    <Box sx={{ ...connectorLineSx, width: '1px', height: '20px' }} />
                  )}

                  <UnitOrgNode
                    depth={depth + 1}
                    onCreateChild={onCreateChild}
                    onDeactivate={onDeactivate}
                    onOpenMemberDialog={onOpenMemberDialog}
                    onOpenUnitDetails={onOpenUnitDetails}
                    onRename={onRename}
                    showMembers={showMembers}
                    showPrimaryActions={showPrimaryActions}
                    unit={child}
                  />
                </Box>
              );
            })}
          </Box>
        </Box>
      ) : null}
    </Box>
  );
};
