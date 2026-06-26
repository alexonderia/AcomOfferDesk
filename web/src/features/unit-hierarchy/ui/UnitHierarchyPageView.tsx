import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import ApartmentOutlinedIcon from '@mui/icons-material/ApartmentOutlined';
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import DeviceHubOutlinedIcon from '@mui/icons-material/DeviceHubOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import Groups2OutlinedIcon from '@mui/icons-material/Groups2Outlined';
import SwapHorizRoundedIcon from '@mui/icons-material/SwapHorizRounded';
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
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useEffect, useMemo, useState } from 'react';
import type { UnitMember, UnitNode } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';
import { useUnitHierarchyPage } from '../model/useUnitHierarchyPage';
import { UnitOrgChart } from './UnitOrgChart';
import {
  getMemberDisplayName,
  getUnitLevelLabel,
  hierarchyCanvasBackground,
  hierarchyPageColors,
  sectionCardSx,
  statusLabelByCode,
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
      ? 'Создать дочерний юнит'
      : 'Редактировать юнит';

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
              renderInput={(params) => <TextField {...params} label="Родительский юнит" />}
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

const PeopleList = ({
  emptyLabel,
  members,
  onMove,
  onRemove,
  title,
}: {
  emptyLabel: string;
  members: UnitMember[];
  onMove?: ((member: UnitMember) => void) | undefined;
  onRemove?: ((member: UnitMember) => void) | undefined;
  title: string;
}) => (
  <Stack spacing={1.1}>
    <Typography sx={{ fontSize: 14, fontWeight: 700 }}>{title}</Typography>
    {members.length === 0 ? (
      <Box
        sx={{
          borderRadius: 2,
          border: '1px dashed',
          borderColor: alpha(hierarchyPageColors.canvasBorder, 0.88),
          backgroundColor: alpha(hierarchyPageColors.canvas, 0.72),
          px: 1.25,
          py: 1.2,
        }}
      >
        <Typography variant="body2" color="text.secondary">
          {emptyLabel}
        </Typography>
      </Box>
    ) : (
      <Stack spacing={0.9}>
        {members.map((member) => (
          <Card key={`${title}-${member.user_id}`} variant="outlined" sx={{ boxShadow: 'none' }}>
            <CardContent
              sx={{
                p: 1.25,
                '&:last-child': { pb: 1.25 },
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                gap: 1,
              }}
            >
              <Box sx={{ minWidth: 0 }}>
                <Typography sx={{ fontSize: 13.5, fontWeight: 700, lineHeight: 1.25, overflowWrap: 'anywhere' }}>
                  {getMemberDisplayName(member)}
                </Typography>
                <Typography variant="caption" sx={{ display: 'block', mt: 0.2, color: 'text.primary' }}>
                  {member.role_name}
                </Typography>
                <Typography variant="caption" sx={{ display: 'block', mt: 0.35, color: 'text.secondary' }}>
                  {statusLabelByCode[member.status] ?? member.status} • {member.user_id}
                </Typography>
              </Box>

              {(onMove || onRemove) ? (
                <Stack direction="row" spacing={0.5}>
                  {onMove ? (
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<SwapHorizRoundedIcon sx={{ fontSize: 16 }} />}
                      onClick={() => onMove(member)}
                      sx={{ textTransform: 'none' }}
                    >
                      Переместить
                    </Button>
                  ) : null}
                  {onRemove ? (
                    <Button
                      size="small"
                      color="error"
                      variant="text"
                      onClick={() => onRemove(member)}
                      sx={{ textTransform: 'none' }}
                    >
                      Открепить
                    </Button>
                  ) : null}
                </Stack>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </Stack>
    )}
  </Stack>
);

const DepartmentOverviewCard = ({
  isActive,
  onOpen,
  onSelect,
  staffCount,
  title,
  unit,
}: {
  isActive: boolean;
  onOpen: () => void;
  onSelect: () => void;
  staffCount: number;
  title: string;
  unit: UnitNode;
}) => {
  const contractorCount = unit.members.filter((member) => member.role_id === ROLE.CONTRACTOR).length;

  return (
    <Card
      variant="outlined"
      sx={{
        ...sectionCardSx,
        borderColor: isActive ? alpha(hierarchyPageColors.softBlue, 0.36) : alpha(hierarchyPageColors.canvasBorder, 0.9),
        boxShadow: isActive ? '0 6px 16px rgba(37, 99, 235, 0.08)' : sectionCardSx.boxShadow,
      }}
    >
      <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Stack spacing={1.1}>
          <Box>
            <Typography variant="caption" sx={{ color: hierarchyPageColors.textSecondary, fontWeight: 700 }}>
              Подразделение
            </Typography>
            <Typography sx={{ mt: 0.35, fontSize: 15, fontWeight: 700, color: hierarchyPageColors.textPrimary }}>
              {title}
            </Typography>
          </Box>

          <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
            <Chip size="small" label={`Сотрудники: ${staffCount}`} />
            <Chip size="small" label={`Юниты 2 уровня: ${unit.children.length}`} />
            <Chip size="small" label={`Контрагенты: ${contractorCount}`} />
          </Stack>

          <Stack direction="row" spacing={0.75}>
            <Button size="small" variant={isActive ? 'contained' : 'outlined'} onClick={onSelect}>
              Выбрать
            </Button>
            {unit.children.length > 0 ? (
              <Button size="small" variant="text" onClick={onOpen}>
                Открыть граф
              </Button>
            ) : null}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
};

const countUniqueMembersInTree = (unit: UnitNode, includeContractors: boolean) => {
  const ids = new Set<string>();
  const visit = (node: UnitNode) => {
    node.members.forEach((member) => {
      const isContractor = member.role_id === ROLE.CONTRACTOR;
      if (includeContractors === isContractor) {
        ids.add(member.user_id);
      }
    });
    node.children.forEach(visit);
  };
  visit(unit);
  return ids.size;
};

const SecondLevelUnitCard = ({
  onEdit,
  onOpen,
  title,
  unit,
}: {
  onEdit: () => void;
  onOpen: () => void;
  title: string;
  unit: UnitNode;
}) => (
  <Card variant="outlined" sx={sectionCardSx}>
    <CardContent sx={{ p: 1.4, '&:last-child': { pb: 1.4 } }}>
      <Stack spacing={1.1}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
          <Box sx={{ minWidth: 0 }}>
            <Typography sx={{ fontSize: 14.5, fontWeight: 700, lineHeight: 1.25, overflowWrap: 'anywhere' }}>
              {title}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {unit.children.length > 0 ? `Вложенных юнитов: ${unit.children.length}` : 'Пока без вложенных юнитов'}
            </Typography>
          </Box>
          <Button size="small" startIcon={<EditOutlinedIcon sx={{ fontSize: 16 }} />} onClick={onEdit}>
            Изменить
          </Button>
        </Stack>

        <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
          <Chip size="small" label={`Сотрудники: ${countUniqueMembersInTree(unit, false)}`} />
          <Chip size="small" label={`Контрагенты: ${countUniqueMembersInTree(unit, true)}`} />
        </Stack>

        <Button variant="contained" startIcon={<DeviceHubOutlinedIcon />} onClick={onOpen}>
          Открыть редактор графа
        </Button>
      </Stack>
    </CardContent>
  </Card>
);

export const UnitHierarchyPageView = () => {
  const {
    departments,
    isLoading,
    error,
    selectedDepartment,
    selectedDepartmentId,
    setSelectedDepartmentId,
    setSelectedEditorUnitId,
    editorRootUnit,
    departmentStaff,
    departmentContractors,
    canCreateRootUnit,
    activeUnitDetails,
    activeUnitParent,
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
    moveMemberState,
    moveUnitOptions,
    setMoveMemberState,
    isMovingMember,
    openMoveMemberDialog,
    closeMoveMemberDialog,
    submitMoveMember,
    deleteDialogState,
    isDeletingUnit,
    openDeleteDialog,
    closeDeleteDialog,
    confirmDeleteUnit,
    findRootUnitForUnit,
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

  if (isLoading) {
    return (
      <Box sx={{ minHeight: 360, display: 'grid', placeItems: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.2 }}>
      <Card
        variant="outlined"
        sx={{
          ...sectionCardSx,
          backgroundImage: hierarchyCanvasBackground,
          borderColor: alpha(hierarchyPageColors.canvasBorder, 0.95),
        }}
      >
        <CardContent sx={{ p: { xs: 1.5, md: 2 }, '&:last-child': { pb: { xs: 1.5, md: 2 } } }}>
          <Stack direction={{ xs: 'column', lg: 'row' }} spacing={1.5} justifyContent="space-between">
            <Box sx={{ maxWidth: 840 }}>
              <Typography variant="caption" sx={{ fontWeight: 700, color: hierarchyPageColors.softBlue }}>
                Иерархия подразделений
              </Typography>
              <Typography sx={{ mt: 0.45, fontSize: { xs: 22, md: 28 }, fontWeight: 800, color: hierarchyPageColors.textPrimary }}>
                Подразделение как корневой юнит, внутри которого живет граф дочерних юнитов
              </Typography>
              <Typography sx={{ mt: 0.7, color: hierarchyPageColors.textSecondary, maxWidth: 760 }}>
                На этом экране мы управляем подразделениями, юнитами второго уровня и вложенным графом.
                Сотрудников сначала закрепляем за нужным юнитом, а контрагентов удерживаем на уровне подразделения.
              </Typography>
            </Box>

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={0.9} alignItems={{ xs: 'stretch', sm: 'center' }}>
              {canCreateRootUnit ? (
                <Button variant="contained" startIcon={<ApartmentOutlinedIcon />} onClick={openCreateRootDialog}>
                  Новое подразделение
                </Button>
              ) : null}
              {selectedDepartment ? (
                <Button
                  variant="outlined"
                  startIcon={<AddOutlinedIcon />}
                  onClick={() => openCreateChildDialog(selectedDepartment)}
                >
                  Юнит второго уровня
                </Button>
              ) : null}
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', xl: '320px minmax(0, 1fr)' } }}>
        <Stack spacing={1.2}>
          {departments.length === 0 ? (
            <Card variant="outlined" sx={sectionCardSx}>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  Пока нет подразделений. Создайте первое корневое подразделение, и затем внутри него можно будет строить граф юнитов.
                </Typography>
              </CardContent>
            </Card>
          ) : (
            departments.map((department) => (
              <DepartmentOverviewCard
                key={department.unit_id}
                isActive={department.unit_id === selectedDepartmentId}
                onOpen={() => {
                  if (department.children[0]) {
                    setSelectedEditorUnitId(department.children[0].unit_id);
                  }
                  setSelectedDepartmentId(department.unit_id);
                }}
                onSelect={() => {
                  setSelectedDepartmentId(department.unit_id);
                  setSelectedEditorUnitId(null);
                }}
                staffCount={countUniqueMembersInTree(department, false)}
                title={department.name}
                unit={department}
              />
            ))
          )}
        </Stack>

        <Stack spacing={2}>
          {selectedDepartment ? (
            !editorRootUnit ? (
              <>
                <Card variant="outlined" sx={sectionCardSx}>
                  <CardContent sx={{ p: 1.7, '&:last-child': { pb: 1.7 } }}>
                    <Stack spacing={1.2}>
                      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} justifyContent="space-between">
                        <Box>
                          <Typography variant="caption" sx={{ color: hierarchyPageColors.textSecondary, fontWeight: 700 }}>
                            Выбранное подразделение
                          </Typography>
                          <Typography sx={{ mt: 0.4, fontSize: 22, fontWeight: 800 }}>
                            {selectedDepartment.name}
                          </Typography>
                        </Box>
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={0.8}>
                          <Button variant="outlined" startIcon={<EditOutlinedIcon />} onClick={() => openEditUnitDialog(selectedDepartment)}>
                            Изменить
                          </Button>
                          <Button variant="contained" startIcon={<DeviceHubOutlinedIcon />} onClick={() => openCreateChildDialog(selectedDepartment)}>
                            Добавить юнит
                          </Button>
                        </Stack>
                      </Stack>

                      <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                        <Chip label={`Сотрудники подразделения: ${departmentStaff.length}`} />
                        <Chip label={`Контрагенты подразделения: ${departmentContractors.length}`} />
                        <Chip label={`Юниты 2 уровня: ${selectedDepartment.children.length}`} />
                      </Stack>
                    </Stack>
                  </CardContent>
                </Card>

                <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', lg: '1.4fr 1fr' } }}>
                  <Card variant="outlined" sx={sectionCardSx}>
                    <CardContent sx={{ p: 1.6, '&:last-child': { pb: 1.6 } }}>
                      <PeopleList
                        emptyLabel="В подразделении пока нет сотрудников."
                        members={departmentStaff}
                        title="Сотрудники подразделения"
                      />
                    </CardContent>
                  </Card>

                  <Card variant="outlined" sx={sectionCardSx}>
                    <CardContent sx={{ p: 1.6, '&:last-child': { pb: 1.6 } }}>
                      <PeopleList
                        emptyLabel="Контрагенты к подразделению пока не привязаны."
                        members={departmentContractors}
                        title="Контрагенты подразделения"
                      />
                    </CardContent>
                  </Card>
                </Box>

                <Card variant="outlined" sx={sectionCardSx}>
                  <CardContent sx={{ p: 1.6, '&:last-child': { pb: 1.6 } }}>
                    <Stack spacing={1.2}>
                      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} justifyContent="space-between">
                        <Box>
                          <Typography sx={{ fontSize: 16, fontWeight: 800 }}>Юниты второго уровня</Typography>
                          <Typography variant="body2" color="text.secondary">
                            Каждый такой юнит открывает собственный редактор вложенного графа.
                          </Typography>
                        </Box>
                        <Button
                          variant="outlined"
                          startIcon={<AddOutlinedIcon />}
                          onClick={() => openCreateChildDialog(selectedDepartment)}
                        >
                          Новый юнит
                        </Button>
                      </Stack>

                      {selectedDepartment.children.length === 0 ? (
                        <Box
                          sx={{
                            borderRadius: 2,
                            border: '1px dashed',
                            borderColor: alpha(hierarchyPageColors.softTeal, 0.34),
                            backgroundColor: alpha(hierarchyPageColors.softTeal, 0.04),
                            px: 1.4,
                            py: 1.6,
                          }}
                        >
                          <Stack spacing={1}>
                            <Typography sx={{ fontSize: 15, fontWeight: 700 }}>Пока нет юнитов второго уровня</Typography>
                            <Typography variant="body2" color="text.secondary">
                              Создайте первый юнит внутри подразделения и затем уже на его уровне стройте нужную иерархию.
                            </Typography>
                          </Stack>
                        </Box>
                      ) : (
                        <Box sx={{ display: 'grid', gap: 1.2, gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))' } }}>
                          {selectedDepartment.children.map((unit) => (
                            <SecondLevelUnitCard
                              key={unit.unit_id}
                              onEdit={() => openEditUnitDialog(unit)}
                              onOpen={() => setSelectedEditorUnitId(unit.unit_id)}
                              title={unit.name}
                              unit={unit}
                            />
                          ))}
                        </Box>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', xl: 'minmax(0, 1fr) 360px' } }}>
                <Stack spacing={2}>
                  <Card variant="outlined" sx={sectionCardSx}>
                    <CardContent sx={{ p: 1.6, '&:last-child': { pb: 1.6 } }}>
                      <Stack spacing={1.2}>
                        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} justifyContent="space-between">
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Button
                              variant="text"
                              startIcon={<ArrowBackRoundedIcon />}
                              onClick={() => {
                                setSelectedEditorUnitId(null);
                                setActiveUnitDetailsId(null);
                              }}
                            >
                              К обзору подразделения
                            </Button>
                            <Divider orientation="vertical" flexItem />
                            <Box>
                              <Typography variant="caption" sx={{ color: hierarchyPageColors.textSecondary, fontWeight: 700 }}>
                                Граф юнита
                              </Typography>
                              <Typography sx={{ mt: 0.2, fontSize: 20, fontWeight: 800 }}>
                                {editorRootUnit.name}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Подразделение: {editorDepartment?.name ?? 'Не определено'}
                              </Typography>
                            </Box>
                          </Stack>

                          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={0.8}>
                            <Button
                              variant="outlined"
                              startIcon={<EditOutlinedIcon />}
                              onClick={() => openEditUnitDialog(editorRootUnit)}
                            >
                              Изменить юнит
                            </Button>
                            <Button
                              variant="contained"
                              startIcon={<AddOutlinedIcon />}
                              onClick={() => openCreateChildDialog(editorRootUnit)}
                            >
                              Добавить дочерний лист
                            </Button>
                          </Stack>
                        </Stack>

                        <Alert severity="info" variant="outlined">
                          Внутри редактора каждый узел можно переименовать, удалить, пополнить сотрудниками и развернуть глубже через дочерние юниты.
                        </Alert>
                      </Stack>
                    </CardContent>
                  </Card>

                  <UnitOrgChart
                    tree={[editorRootUnit]}
                    onCreateChild={openCreateChildDialog}
                    onDelete={openDeleteDialog}
                    onOpenMemberDialog={openMemberDialog}
                    onOpenUnitDetails={(unit) => setActiveUnitDetailsId(unit.unit_id)}
                    onRename={openEditUnitDialog}
                  />
                </Stack>

                <Card
                  variant="outlined"
                  sx={{
                    ...sectionCardSx,
                    alignSelf: 'start',
                    position: { xl: 'sticky' },
                    top: { xl: 16 },
                  }}
                >
                  <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                    {activeUnitDetails ? (
                      <Stack spacing={1.35}>
                        <Box>
                          <Typography variant="caption" sx={{ color: hierarchyPageColors.textSecondary, fontWeight: 700 }}>
                            {getUnitLevelLabel(activeUnitDetails.id_parent === null ? 0 : 1)}
                          </Typography>
                          <Typography sx={{ mt: 0.25, fontSize: 18, fontWeight: 800 }}>
                            {activeUnitDetails.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {activeUnitPathLabel}
                          </Typography>
                        </Box>

                        <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                          <Chip label={`Сотрудники: ${detailStaff.length}`} />
                          <Chip label={`Контрагенты: ${detailContractors.length}`} />
                          <Chip label={`Дочерние юниты: ${activeUnitDetails.children.length}`} />
                        </Stack>

                        <Stack direction="row" spacing={0.75}>
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<EditOutlinedIcon sx={{ fontSize: 16 }} />}
                            onClick={() => openEditUnitDialog(activeUnitDetails)}
                          >
                            Изменить
                          </Button>
                          {activeUnitDetails.actions.canDelete ? (
                            <Button
                              size="small"
                              color="error"
                              variant="text"
                              onClick={() => openDeleteDialog(activeUnitDetails)}
                            >
                              Удалить
                            </Button>
                          ) : null}
                        </Stack>

                        <Divider />

                        <Box>
                          <Typography variant="caption" sx={{ color: hierarchyPageColors.textSecondary, fontWeight: 700 }}>
                            Родительский юнит
                          </Typography>
                          <Typography sx={{ mt: 0.3, fontSize: 14.5, fontWeight: 700 }}>
                            {activeUnitParent?.name ?? 'Корневое подразделение'}
                          </Typography>
                        </Box>

                        <Button
                          variant="contained"
                          startIcon={<Groups2OutlinedIcon />}
                          onClick={() => openMemberDialog(activeUnitDetails)}
                        >
                          Добавить сотрудника
                        </Button>

                        <PeopleList
                          emptyLabel="В этом юните пока нет сотрудников."
                          members={detailStaff}
                          onMove={(member) => openMoveMemberDialog(activeUnitDetails, member)}
                          onRemove={(member) => {
                            void removeMemberFromUnit(activeUnitDetails, member);
                          }}
                          title="Сотрудники юнита"
                        />

                        {detailContractors.length > 0 ? (
                          <PeopleList
                            emptyLabel=""
                            members={detailContractors}
                            title="Контрагенты в узле"
                          />
                        ) : null}
                      </Stack>
                    ) : (
                      <Stack spacing={1.1}>
                        <Typography sx={{ fontSize: 16, fontWeight: 800 }}>Детали юнита</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Кликните по карточке юнита в графе, чтобы открыть его состав, увидеть родителя и быстро добавить сотрудников или дочерние листы.
                        </Typography>
                      </Stack>
                    )}
                  </CardContent>
                </Card>
              </Box>
            )
          ) : (
            <Card variant="outlined" sx={sectionCardSx}>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  Выберите подразделение слева, чтобы открыть его обзор или редактор графа.
                </Typography>
              </CardContent>
            </Card>
          )}
        </Stack>
      </Box>

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
        <DialogTitle>Добавить сотрудника в юнит</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={1.35}>
            <Typography variant="body2" color="text.secondary">
              Сначала выбираем юнит, затем закрепляем за ним сотрудника. Контрагенты в этом потоке не участвуют.
            </Typography>
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
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeMemberDialog}>Отмена</Button>
          <Button variant="contained" disabled={isSavingMember || !memberDialogState.selectedUserId} onClick={() => void submitMember()}>
            {isSavingMember ? 'Добавляем...' : 'Добавить'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(moveMemberState)} onClose={closeMoveMemberDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Перенести сотрудника в другой юнит</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={1.35}>
            <Typography variant="body2" color="text.secondary">
              Сотрудник будет добавлен в целевой юнит и откреплен от текущего.
            </Typography>
            <Autocomplete
              options={moveUnitOptions}
              value={selectedMoveTarget}
              onChange={(_event, value) => {
                setMoveMemberState((current) => current ? { ...current, targetUnitId: value?.unitId ?? null } : current);
              }}
              getOptionLabel={(option) => option.label}
              isOptionEqualToValue={(option, value) => option.unitId === value.unitId}
              renderInput={(params) => <TextField {...params} label="Целевой юнит" />}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeMoveMemberDialog}>Отмена</Button>
          <Button variant="contained" disabled={isMovingMember || !moveMemberState?.targetUnitId} onClick={() => void submitMoveMember()}>
            {isMovingMember ? 'Переносим...' : 'Перенести'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(deleteDialogState)} onClose={closeDeleteDialog} maxWidth="lg" fullWidth>
        <DialogTitle>Удаление юнита</DialogTitle>
        <DialogContent dividers>
          {deleteDialogState ? (
            <Stack spacing={1.4}>
              <Alert severity={deleteDialogState.willReassign ? 'warning' : 'info'} variant="outlined">
                {deleteDialogState.willReassign
                  ? 'Удаление перенесет прямых сотрудников в родительский юнит и поднимет дочерние узлы на уровень выше.'
                  : 'Юнит будет удален без переноса сотрудников.'}
              </Alert>

              <Box>
                <Typography sx={{ fontSize: 15, fontWeight: 700 }}>{deleteDialogState.unit.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  После подтверждения экран отобразит уже обновленную структуру.
                </Typography>
              </Box>

              <Box>
                <Typography sx={{ mb: 1, fontSize: 14, fontWeight: 700 }}>Предпросмотр новой иерархии</Typography>
                <UnitOrgChart
                  tree={deleteDialogState.previewTree}
                  onCreateChild={() => {}}
                  onDelete={() => {}}
                  onRename={() => {}}
                  showPrimaryActions={false}
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
