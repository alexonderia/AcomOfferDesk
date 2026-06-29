import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import ApartmentOutlinedIcon from '@mui/icons-material/ApartmentOutlined';
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import DeviceHubOutlinedIcon from '@mui/icons-material/DeviceHubOutlined';
import GroupAddOutlinedIcon from '@mui/icons-material/GroupAddOutlined';
import HandshakeOutlinedIcon from '@mui/icons-material/HandshakeOutlined';
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
  Divider,
  IconButton,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useEffect, useMemo, useState } from 'react';
import type { UnitNode } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';
import { useToastMessageEffect } from '@shared/ui/toasts';
import { useUnitHierarchyPage } from '../model/useUnitHierarchyPage';
import { ContractorBindingsDialog } from './ContractorBindingsDialog';
import { PeopleFlatList, PeopleTree } from './PeopleTree';
import { UnitOrgChart } from './UnitOrgChart';
import {
  hierarchyCanvasBackground,
  hierarchyPageColors,
  outlinedIconButtonSx,
  sectionCardSx,
} from './unitHierarchyStyles';

type UnitFormDialogProps = {
  isSaving: boolean;
  mode: 'create-root' | 'create-child' | 'edit';
  open: boolean;
  parentOptions: Array<{ unitId: number; label: string }>;
  unit: UnitNode | null;
  onClose: () => void;
  onSubmit: (payload: { name: string; parentUnitId?: number | null }) => Promise<void>;
};

const UnitFormDialog = ({
  isSaving,
  mode,
  open,
  parentOptions,
  unit,
  onClose,
  onSubmit,
}: UnitFormDialogProps) => {
  const [name, setName] = useState('');
  const [parentUnitId, setParentUnitId] = useState<number | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    setName(unit?.name ?? '');
    setParentUnitId(unit?.id_parent ?? null);
  }, [open, unit]);

  const title = mode === 'create-root'
    ? 'Создать подразделение'
    : mode === 'create-child'
      ? 'Создать дочерний лист'
      : 'Редактировать лист';

  const selectedParentOption = parentOptions.find((option) => option.unitId === parentUnitId) ?? null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          <TextField
            autoFocus
            fullWidth
            label="Название"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
          {mode === 'edit' && unit?.id_parent !== null ? (
            <Autocomplete
              options={parentOptions}
              value={selectedParentOption}
              onChange={(_event, value) => setParentUnitId(value?.unitId ?? null)}
              getOptionLabel={(option) => option.label}
              isOptionEqualToValue={(option, value) => option.unitId === value.unitId}
              renderInput={(params) => <TextField {...params} label="Родительский лист" />}
            />
          ) : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отмена</Button>
        <Button
          variant="contained"
          disabled={isSaving}
          onClick={() => {
            void onSubmit({ name, parentUnitId });
          }}
        >
          {isSaving ? 'Сохраняем...' : 'Сохранить'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const collectUniqueMembers = (unit: UnitNode, includeContractors: boolean) => {
  const byUserId = new Map<string, UnitNode['members'][number]>();
  const visit = (node: UnitNode) => {
    node.members.forEach((member) => {
      const isContractor = member.role_id === ROLE.CONTRACTOR;
      if (includeContractors !== isContractor) {
        return;
      }
      if (!byUserId.has(member.user_id)) {
        byUserId.set(member.user_id, member);
      }
    });
    node.children.forEach(visit);
  };
  visit(unit);
  return [...byUserId.values()];
};

const UnitStatTile = ({
  color,
  label,
  value,
}: {
  color: string;
  label: string;
  value: number;
}) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'baseline',
      gap: 0.5,
      borderRadius: 1.5,
      border: `1px solid ${alpha(color, 0.22)}`,
      backgroundColor: alpha(color, 0.06),
      px: 0.9,
      py: 0.35,
    }}
  >
    <Typography sx={{ fontSize: 13, fontWeight: 800, lineHeight: 1, color }}>
      {value}
    </Typography>
    <Typography sx={{ fontSize: 11, fontWeight: 600, lineHeight: 1, color: hierarchyPageColors.textSecondary, whiteSpace: 'nowrap' }}>
      {label}
    </Typography>
  </Box>
);

const UnitStatRow = ({
  childrenCount,
  contractorCount,
  staffCount,
}: {
  childrenCount?: number | undefined;
  contractorCount: number;
  staffCount: number;
}) => (
  <Stack direction="row" spacing={0.7} useFlexGap flexWrap="wrap" sx={{ minWidth: 0 }}>
    <UnitStatTile color={hierarchyPageColors.softTeal} label="Сотрудники" value={staffCount} />
    <UnitStatTile color={hierarchyPageColors.softPink} label="Контрагенты" value={contractorCount} />
    {childrenCount !== undefined ? (
      <UnitStatTile color={hierarchyPageColors.softBlue} label="Дочерние" value={childrenCount} />
    ) : null}
  </Stack>
);

const SecondLevelUnitBlock = ({
  onOpen,
  unit,
}: {
  onOpen: () => void;
  unit: UnitNode;
}) => {
  const staffCount = collectUniqueMembers(unit, false).length;
  const contractorCount = collectUniqueMembers(unit, true).length;

  return (
    <Box
      role="button"
      tabIndex={0}
      aria-label={`Открыть редактор листа ${unit.name}`}
      onClick={onOpen}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onOpen();
        }
      }}
      sx={{
        cursor: 'pointer',
        borderRadius: 2.5,
        border: `1px solid ${alpha(hierarchyPageColors.cardBorder, 0.98)}`,
        backgroundColor: '#ffffff',
        boxShadow: hierarchyPageColors.shadow,
        px: 1.4,
        py: 1.25,
        transition: 'border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease',
        '&:hover': {
          borderColor: alpha(hierarchyPageColors.softBlue, 0.5),
          boxShadow: '0 6px 16px rgba(37, 99, 235, 0.12)',
          transform: 'translateY(-1px)',
        },
        '&:focus-visible': {
          outline: `2px solid ${alpha(hierarchyPageColors.softBlue, 0.55)}`,
          outlineOffset: 2,
        },
      }}
    >
      <Stack direction="row" spacing={1} alignItems="flex-start" justifyContent="space-between">
        <Box sx={{ minWidth: 0 }}>
          <Typography sx={{ fontSize: 15, fontWeight: 700, lineHeight: 1.24, overflowWrap: 'anywhere' }}>
            {unit.name}
          </Typography>
          <Stack direction="row" spacing={0.6} useFlexGap flexWrap="wrap" sx={{ mt: 0.8 }}>
            <Chip size="small" label={`Сотрудники: ${staffCount}`} />
            <Chip size="small" label={`Вложенные: ${unit.children.length}`} />
            {contractorCount > 0 ? <Chip size="small" label={`Контрагенты: ${contractorCount}`} /> : null}
          </Stack>
        </Box>
        <Tooltip title="Открыть схему и редактор">
          <DeviceHubOutlinedIcon sx={{ color: hierarchyPageColors.softBlue, fontSize: 20, flexShrink: 0 }} />
        </Tooltip>
      </Stack>
    </Box>
  );
};

const DepartmentGraphCard = ({
  canManage,
  department,
  onAddContractor,
  onAddUnit,
  onEdit,
  onOpenUnit,
  onRemoveContractor,
}: {
  canManage: boolean;
  department: UnitNode;
  onAddContractor: () => void;
  onAddUnit: () => void;
  onEdit: () => void;
  onOpenUnit: (unit: UnitNode) => void;
  onRemoveContractor: (member: UnitNode['members'][number]) => void;
}) => {
  const staff = collectUniqueMembers(department, false);
  const contractors = collectUniqueMembers(department, true);

  return (
    <Card variant="outlined" sx={sectionCardSx}>
      <CardContent sx={{ p: { xs: 1.25, md: 1.75 }, '&:last-child': { pb: { xs: 1.25, md: 1.75 } } }}>
        <Box
          sx={{
            borderRadius: 3,
            border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
            backgroundImage: hierarchyCanvasBackground,
            p: { xs: 1.1, md: 1.6 },
          }}
        >
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1}
            justifyContent="space-between"
            alignItems={{ xs: 'flex-start', sm: 'center' }}
          >
            <Box sx={{ minWidth: 0 }}>
              <Typography sx={{ fontSize: { xs: 18, md: 21 }, fontWeight: 800, overflowWrap: 'anywhere' }}>
                {department.name}
              </Typography>
            </Box>
            {canManage ? (
              <Stack direction="row" spacing={0.8} sx={{ flexShrink: 0 }} useFlexGap flexWrap="wrap">
                <Button size="small" variant="outlined" startIcon={<ApartmentOutlinedIcon sx={{ fontSize: 16 }} />} onClick={onEdit}>
                  Изменить
                </Button>
                <Button size="small" variant="outlined" startIcon={<HandshakeOutlinedIcon sx={{ fontSize: 16 }} />} onClick={onAddContractor}>
                  Добавить контрагента
                </Button>
                <Button size="small" variant="contained" startIcon={<AddOutlinedIcon sx={{ fontSize: 16 }} />} onClick={onAddUnit}>
                  Добавить лист
                </Button>
              </Stack>
            ) : null}
          </Stack>

          <Box sx={{ mt: 1, maxWidth: 360 }}>
            <UnitStatRow contractorCount={contractors.length} staffCount={staff.length} />
          </Box>

          <Box
            sx={{
              mt: 1.4,
              display: 'grid',
              gap: 1.4,
              gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 1fr) minmax(0, 300px)' },
              alignItems: 'start',
            }}
          >
            <Box sx={{ minWidth: 0 }}>
              {department.children.length === 0 ? (
                <Stack
                  spacing={1}
                  alignItems="flex-start"
                  sx={{
                    borderRadius: 2.5,
                    border: `1px dashed ${alpha(hierarchyPageColors.softTeal, 0.4)}`,
                    backgroundColor: alpha(hierarchyPageColors.softTeal, 0.05),
                    px: 1.4,
                    py: 1.5,
                  }}
                >
                  <Typography sx={{ fontSize: 14, fontWeight: 700 }}>Пока нет листов</Typography>
                  {canManage ? (
                    <Button size="small" variant="outlined" startIcon={<AddOutlinedIcon />} onClick={onAddUnit}>
                      Создать лист
                    </Button>
                  ) : null}
                </Stack>
              ) : (
                <Box
                  sx={{
                    display: 'grid',
                    gap: 1,
                    gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' },
                  }}
                >
                  {department.children.map((unit) => (
                    <SecondLevelUnitBlock key={unit.unit_id} onOpen={() => onOpenUnit(unit)} unit={unit} />
                  ))}
                  {canManage ? (
                    <Box
                      role="button"
                      tabIndex={0}
                      aria-label="Добавить лист второго уровня"
                      onClick={onAddUnit}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault();
                          onAddUnit();
                        }
                      }}
                      sx={{
                        cursor: 'pointer',
                        display: 'grid',
                        placeItems: 'center',
                        minHeight: 84,
                        borderRadius: 2.5,
                        border: `1px dashed ${alpha(hierarchyPageColors.softBlue, 0.4)}`,
                        backgroundColor: alpha(hierarchyPageColors.softBlue, 0.04),
                        color: hierarchyPageColors.softBlue,
                        transition: 'background-color 0.16s ease',
                        '&:hover': { backgroundColor: alpha(hierarchyPageColors.softBlue, 0.08) },
                        '&:focus-visible': {
                          outline: `2px solid ${alpha(hierarchyPageColors.softBlue, 0.55)}`,
                          outlineOffset: 2,
                        },
                      }}
                    >
                      <Stack spacing={0.3} alignItems="center">
                        <AddOutlinedIcon />
                        <Typography sx={{ fontSize: 12.5, fontWeight: 700 }}>Новый лист</Typography>
                      </Stack>
                    </Box>
                  ) : null}
                </Box>
              )}
            </Box>

            <Stack spacing={1.4} sx={{ minWidth: 0 }}>
              <PeopleTree
                emptyLabel="Сотрудников пока нет."
                members={staff}
                title="Сотрудники подразделения"
              />
              <PeopleFlatList
                emptyLabel="Контрагентов пока нет."
                members={contractors}
                onRemove={canManage ? onRemoveContractor : undefined}
                title="Контрагенты подразделения"
              />
            </Stack>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export const UnitHierarchyPageView = () => {
  const {
    departments,
    isLoading,
    error,
    setSelectedDepartmentId,
    setSelectedEditorUnitId,
    editorRootUnit,
    canCreateRootUnit,
    activeUnitDetails,
    activeUnitPathLabel,
    setActiveUnitDetailsId,
    unitDialogState,
    isSavingUnit,
    editableParentOptions,
    openCreateRootDialog,
    openCreateChildDialog,
    openEditUnitDialog,
    closeUnitDialog,
    submitUnit,
    memberDialogState,
    setMemberDialogState,
    availableUsers,
    isLoadingUsers,
    isSavingMember,
    openMemberDialog,
    closeMemberDialog,
    submitMember,
    removeMemberFromUnit,
    contractorDialogUnit,
    openContractorDialog,
    closeContractorDialog,
    removeContractorFromUnit,
    moveMemberState,
    moveUnitOptions,
    setMoveMemberState,
    isMovingMember,
    openMoveMemberDialog,
    closeMoveMemberDialog,
    submitMoveMember,
    inlineUnitName,
    setInlineUnitName,
    isSavingInlineUnitName,
    submitInlineUnitName,
    deleteDialogState,
    isDeletingUnit,
    openDeleteDialog,
    closeDeleteDialog,
    confirmDeleteUnit,
    findRootUnitForUnit,
    loadTree,
  } = useUnitHierarchyPage();

  const selectedUser = availableUsers.find((user) => user.user_id === memberDialogState.selectedUserId) ?? null;
  const selectedMoveTarget = moveUnitOptions.find((option) => option.unitId === moveMemberState?.targetUnitId) ?? null;

  const detailStaff = useMemo(
    () => (activeUnitDetails?.members ?? []).filter((member) => member.role_id !== ROLE.CONTRACTOR),
    [activeUnitDetails]
  );
  const detailContractors = useMemo(
    () => (activeUnitDetails?.members ?? []).filter((member) => member.role_id === ROLE.CONTRACTOR),
    [activeUnitDetails]
  );

  const editorDepartment = editorRootUnit ? findRootUnitForUnit(editorRootUnit.unit_id) : null;
  const isEditorOpen = Boolean(editorRootUnit);
  const canEditActiveUnit = Boolean(activeUnitDetails?.actions.canUpdate);
  const hasInlineNameChanges = Boolean(activeUnitDetails && inlineUnitName.trim() && inlineUnitName.trim() !== activeUnitDetails.name);

  useToastMessageEffect({ message: error });

  const openUnitEditor = (unit: UnitNode) => {
    setSelectedEditorUnitId(unit.unit_id);
    setActiveUnitDetailsId(unit.unit_id);
  };

  const closeUnitEditor = () => {
    setSelectedEditorUnitId(null);
    setActiveUnitDetailsId(null);
  };

  const handleAddUnit = (department: UnitNode) => {
    setSelectedDepartmentId(department.unit_id);
    openCreateChildDialog(department);
  };

  if (isLoading) {
    return (
      <Box sx={{ minHeight: 360, display: 'grid', placeItems: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Card variant="outlined" sx={sectionCardSx}>
        <CardContent>
          <Stack spacing={1.5} alignItems="flex-start">
            <Typography variant="body2" color="text.secondary">
              Не удалось загрузить иерархию подразделений.
            </Typography>
            <Button variant="outlined" onClick={() => void loadTree()}>
              Повторить
            </Button>
          </Stack>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {canCreateRootUnit ? (
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button variant="contained" startIcon={<ApartmentOutlinedIcon />} onClick={openCreateRootDialog} sx={{ flexShrink: 0 }}>
            Новое подразделение
          </Button>
        </Box>
      ) : null}

      {departments.length === 0 ? (
        <Card variant="outlined" sx={sectionCardSx}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              Пока нет подразделений. Создайте первое корневое подразделение.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Stack spacing={2}>
          {departments.map((department) => (
            <DepartmentGraphCard
              key={department.unit_id}
              canManage={department.actions.canManageMembers || department.actions.canCreateChild || department.actions.canUpdate}
              department={department}
              onAddContractor={() => openContractorDialog(department)}
              onAddUnit={() => handleAddUnit(department)}
              onEdit={() => openEditUnitDialog(department)}
              onOpenUnit={openUnitEditor}
              onRemoveContractor={(member) => {
                void removeContractorFromUnit(department, member);
              }}
            />
          ))}
        </Stack>
      )}

      <Dialog fullScreen open={isEditorOpen} onClose={closeUnitEditor}>
        {editorRootUnit ? (
          <>
            <DialogTitle sx={{ p: 0 }}>
              <Box
                sx={{
                  px: { xs: 1.25, md: 2 },
                  py: 1.2,
                  borderBottom: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
                  backgroundImage: hierarchyCanvasBackground,
                }}
              >
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} justifyContent="space-between" alignItems={{ md: 'center' }}>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ minWidth: 0 }}>
                    <Tooltip title="Закрыть окно">
                      <IconButton onClick={closeUnitEditor} aria-label="Закрыть редактор" sx={{ flexShrink: 0 }}>
                        <ArrowBackRoundedIcon />
                      </IconButton>
                    </Tooltip>
                    <Box sx={{ minWidth: 0 }}>
                      <Typography variant="caption" sx={{ color: hierarchyPageColors.textSecondary, fontWeight: 700 }} noWrap>
                        Подразделение {editorDepartment?.name ?? 'АО'}
                      </Typography>
                      <Typography sx={{ fontSize: { xs: 17, md: 20 }, fontWeight: 800, lineHeight: 1.2, overflowWrap: 'anywhere' }}>
                        {editorRootUnit.name}
                      </Typography>
                    </Box>
                  </Stack>

                  <Tooltip title="Закрыть окно">
                    <IconButton onClick={closeUnitEditor} aria-label="Закрыть окно редактора">
                      <CloseRoundedIcon />
                    </IconButton>
                  </Tooltip>
                </Stack>
              </Box>
            </DialogTitle>

            <DialogContent sx={{ p: { xs: 1.25, md: 2 }, backgroundColor: alpha(hierarchyPageColors.canvas, 0.4) }}>
              <Box sx={{ display: 'grid', gap: 1.6, gridTemplateColumns: { xs: '1fr', lg: 'minmax(0, 1fr) minmax(0, 340px)' }, mt: 1 }}>
                <Box sx={{ minWidth: 0 }}>
                  <UnitOrgChart
                    fillHeight
                    tree={[editorRootUnit]}
                    onCreateChild={openCreateChildDialog}
                    onDelete={openDeleteDialog}
                    onMoveMember={(unit, member) => openMoveMemberDialog(unit, member)}
                    onOpenMemberDialog={openMemberDialog}
                    onOpenUnitDetails={(unit) => setActiveUnitDetailsId(unit.unit_id)}
                    onRemoveMember={(unit, member) => {
                      void removeMemberFromUnit(unit, member);
                    }}
                  />
                </Box>

                <Card
                  variant="outlined"
                  sx={{
                    ...sectionCardSx,
                    alignSelf: 'start',
                    position: { lg: 'sticky' },
                    top: { lg: 16 },
                  }}
                >
                  <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                    {activeUnitDetails ? (
                      <Stack spacing={1.35} sx={{ minWidth: 0 }}>
                        <Stack spacing={0.8} sx={{ minWidth: 0 }}>
                          <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="center">
                            <Box sx={{ minWidth: 0, flex: 1 }}>
                              {canEditActiveUnit ? (
                                <TextField
                                  fullWidth
                                  size="small"
                                  value={inlineUnitName}
                                  onChange={(event) => setInlineUnitName(event.target.value)}
                                  placeholder="Название"
                                />
                              ) : (
                                <Typography sx={{ fontSize: 18, fontWeight: 800, overflowWrap: 'anywhere' }}>
                                  {activeUnitDetails.name}
                                </Typography>
                              )}
                            </Box>
                            {activeUnitDetails.actions.canDelete ? (
                              <Tooltip title="Удалить">
                                <IconButton
                                  size="small"
                                  onClick={() => openDeleteDialog(activeUnitDetails)}
                                  aria-label={`Удалить ${activeUnitDetails.name}`}
                                  sx={{ ...outlinedIconButtonSx, flexShrink: 0 }}
                                >
                                  <DeleteOutlineRoundedIcon sx={{ fontSize: 18 }} />
                                </IconButton>
                              </Tooltip>
                            ) : null}
                          </Stack>
                          <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
                            {activeUnitPathLabel}
                          </Typography>
                        </Stack>

                        {canEditActiveUnit && hasInlineNameChanges ? (
                          <Button
                            variant="contained"
                            disabled={isSavingInlineUnitName}
                            onClick={() => void submitInlineUnitName()}
                          >
                            {isSavingInlineUnitName ? 'Сохраняем...' : 'Сохранить'}
                          </Button>
                        ) : null}

                        <UnitStatRow
                          childrenCount={activeUnitDetails.children.length}
                          contractorCount={detailContractors.length}
                          staffCount={detailStaff.length}
                        />

                        <Divider />

                        <PeopleTree
                          emptyLabel="В этом листе пока нет сотрудников."
                          headerAction={activeUnitDetails.actions.canManageMembers ? (
                            <Tooltip title="Добавить сотрудника">
                              <IconButton
                                size="small"
                                onClick={() => openMemberDialog(activeUnitDetails)}
                                aria-label={`Добавить сотрудника в ${activeUnitDetails.name}`}
                                sx={outlinedIconButtonSx}
                              >
                                <GroupAddOutlinedIcon sx={{ fontSize: 17 }} />
                              </IconButton>
                            </Tooltip>
                          ) : undefined}
                          members={detailStaff}
                          onMove={(member) => openMoveMemberDialog(activeUnitDetails, member)}
                          onRemove={(member) => {
                            void removeMemberFromUnit(activeUnitDetails, member);
                          }}
                          title="Состав"
                        />

                        {detailContractors.length > 0 ? (
                          <PeopleFlatList
                            emptyLabel=""
                            members={detailContractors}
                            title="Контрагенты"
                          />
                        ) : null}
                      </Stack>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Выберите лист на графе, чтобы открыть состав и статистику.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Box>
            </DialogContent>
          </>
        ) : null}
      </Dialog>

      {unitDialogState.mode ? (
        <UnitFormDialog
          isSaving={isSavingUnit}
          mode={unitDialogState.mode}
          open={Boolean(unitDialogState.mode)}
          parentOptions={editableParentOptions}
          unit={unitDialogState.unit}
          onClose={closeUnitDialog}
          onSubmit={submitUnit}
        />
      ) : null}

      <Dialog open={Boolean(memberDialogState.unit)} onClose={closeMemberDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Добавить сотрудника в лист</DialogTitle>
        <DialogContent dividers>
          <Autocomplete
            options={availableUsers}
            loading={isLoadingUsers}
            value={selectedUser}
            onChange={(_event, value) => {
              setMemberDialogState((current) => ({ ...current, selectedUserId: value?.user_id ?? '' }));
            }}
            inputValue={memberDialogState.search}
            onInputChange={(_event, value) => {
              setMemberDialogState((current) => ({ ...current, search: value }));
            }}
            getOptionLabel={(option) => option.full_name ? `${option.full_name} (${option.user_id})` : option.user_id}
            isOptionEqualToValue={(option, value) => option.user_id === value.user_id}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Сотрудник"
                placeholder="Начните вводить имя или логин"
              />
            )}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeMemberDialog}>Отмена</Button>
          <Button variant="contained" disabled={isSavingMember || !memberDialogState.selectedUserId} onClick={() => void submitMember()}>
            {isSavingMember ? 'Добавляем...' : 'Добавить'}
          </Button>
        </DialogActions>
      </Dialog>

      <ContractorBindingsDialog
        open={Boolean(contractorDialogUnit)}
        departmentName={contractorDialogUnit?.name}
        onClose={closeContractorDialog}
        onSaved={loadTree}
      />

      <Dialog open={Boolean(moveMemberState)} onClose={closeMoveMemberDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Перенести сотрудника в другой лист</DialogTitle>
        <DialogContent dividers>
          <Autocomplete
            options={moveUnitOptions}
            value={selectedMoveTarget}
            onChange={(_event, value) => {
              setMoveMemberState((current) => current ? { ...current, targetUnitId: value?.unitId ?? null } : current);
            }}
            getOptionLabel={(option) => option.label}
            isOptionEqualToValue={(option, value) => option.unitId === value.unitId}
            renderInput={(params) => <TextField {...params} label="Целевой лист" />}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeMoveMemberDialog}>Отмена</Button>
          <Button variant="contained" disabled={isMovingMember || !moveMemberState?.targetUnitId} onClick={() => void submitMoveMember()}>
            {isMovingMember ? 'Переносим...' : 'Перенести'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(deleteDialogState)} onClose={closeDeleteDialog} maxWidth="lg" fullWidth>
        <DialogTitle>Удаление листа</DialogTitle>
        <DialogContent dividers>
          {deleteDialogState ? (
            <Stack spacing={1.4}>
              <Alert severity={deleteDialogState.willReassign ? 'warning' : 'info'} variant="outlined">
                {deleteDialogState.willReassign
                  ? 'Удаление перенесет прямых сотрудников в родительский лист и поднимет дочерние узлы на уровень выше.'
                  : 'Лист будет удален без переноса сотрудников.'}
              </Alert>

              <Typography sx={{ fontSize: 15, fontWeight: 700 }}>{deleteDialogState.unit.name}</Typography>

              <Box>
                <Typography sx={{ mb: 1, fontSize: 14, fontWeight: 700 }}>Предпросмотр новой иерархии</Typography>
                <UnitOrgChart
                  tree={deleteDialogState.previewTree}
                  onCreateChild={() => {}}
                  onDelete={() => {}}
                  showPrimaryActions={false}
                  showZoomControls={false}
                />
              </Box>
            </Stack>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDeleteDialog}>Отмена</Button>
          <Button color="error" variant="contained" disabled={isDeletingUnit} onClick={() => void confirmDeleteUnit()}>
            {isDeletingUnit ? 'Удаляем...' : 'Удалить'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
