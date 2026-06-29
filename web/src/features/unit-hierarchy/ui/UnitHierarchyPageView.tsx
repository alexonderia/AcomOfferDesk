import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import ApartmentOutlinedIcon from '@mui/icons-material/ApartmentOutlined';
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import DeviceHubOutlinedIcon from '@mui/icons-material/DeviceHubOutlined';
import GroupAddOutlinedIcon from '@mui/icons-material/GroupAddOutlined';
import HandshakeOutlinedIcon from '@mui/icons-material/HandshakeOutlined';
import OpenInFullRoundedIcon from '@mui/icons-material/OpenInFullRounded';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
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
import { useDeferredValue, useEffect, useMemo, useState } from 'react';
import type { UnitMember, UnitNode } from '@shared/api/units';
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

type FilteredDepartmentView = {
  department: UnitNode;
  filteredDepartment: UnitNode;
  totalUnits: number;
  visibleUnits: number;
  totalStaff: number;
  visibleStaff: UnitMember[];
  totalContractors: number;
  visibleContractors: UnitMember[];
};

type VisibleUnitRow = {
  depth: number;
  pathLabel: string;
  unit: UnitNode;
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
      : 'Изменить подразделение';

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

const countUnits = (unit: UnitNode): number =>
  1 + unit.children.reduce((sum, child) => sum + countUnits(child), 0);

const normalizeSearch = (value: string) => value.trim().toLocaleLowerCase('ru');

const matchesMemberQuery = (member: UnitMember, normalizedQuery: string) => {
  if (!normalizedQuery) {
    return true;
  }

  const haystack = [
    member.full_name ?? '',
    member.user_id,
    member.role_name,
  ].join(' ').toLocaleLowerCase('ru');

  return haystack.includes(normalizedQuery);
};

const filterUnitTree = (unit: UnitNode, normalizedQuery: string): UnitNode | null => {
  if (!normalizedQuery) {
    return unit;
  }

  const filteredChildren = unit.children
    .map((child) => filterUnitTree(child, normalizedQuery))
    .filter((child): child is UnitNode => child !== null);

  const directMemberMatch = unit.members.some((member) => matchesMemberQuery(member, normalizedQuery));
  const directUnitMatch = unit.name.toLocaleLowerCase('ru').includes(normalizedQuery);

  if (!directMemberMatch && !directUnitMatch && filteredChildren.length === 0) {
    return null;
  }

  return {
    ...unit,
    members: unit.members.filter((member) => matchesMemberQuery(member, normalizedQuery)),
    children: filteredChildren,
  };
};

const buildVisibleUnitRows = (unit: UnitNode, depth = 0, path: string[] = []): VisibleUnitRow[] =>
  unit.children.flatMap((child) => {
    const nextPath = [...path, child.name];
    return [
      {
        depth,
        pathLabel: nextPath.join(' / '),
        unit: child,
      },
      ...buildVisibleUnitRows(child, depth + 1, nextPath),
    ];
  });

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
      <UnitStatTile color={hierarchyPageColors.softBlue} label="Листы" value={childrenCount} />
    ) : null}
  </Stack>
);

const InlineUnitNameField = ({
  canEdit,
  isSaving,
  onSubmit,
  unit,
}: {
  canEdit: boolean;
  isSaving: boolean;
  onSubmit: (unit: UnitNode, nextName: string) => Promise<void>;
  unit: UnitNode;
}) => {
  const [draft, setDraft] = useState(unit.name);

  useEffect(() => {
    setDraft(unit.name);
  }, [unit.name, unit.unit_id]);

  const commit = async () => {
    const normalized = draft.trim();
    if (!normalized) {
      setDraft(unit.name);
      return;
    }
    if (normalized === unit.name) {
      return;
    }
    await onSubmit(unit, normalized);
  };

  if (!canEdit) {
    return (
      <Typography sx={{ fontSize: { xs: 18, md: 21 }, fontWeight: 800, lineHeight: 1.2, overflowWrap: 'anywhere' }}>
        {unit.name}
      </Typography>
    );
  }

  return (
    <TextField
      fullWidth
      size="small"
      value={draft}
      onBlur={() => {
        void commit();
      }}
      onChange={(event) => setDraft(event.target.value)}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          void commit();
          event.currentTarget.blur();
        }
        if (event.key === 'Escape') {
          setDraft(unit.name);
          event.currentTarget.blur();
        }
      }}
      placeholder="Название подразделения"
      inputProps={{ 'aria-label': `Название подразделения ${unit.name}` }}
      InputProps={{
        endAdornment: isSaving ? <CircularProgress size={15} /> : null,
      }}
      sx={{
        '& .MuiOutlinedInput-root': {
          borderRadius: 2,
          backgroundColor: alpha('#ffffff', 0.92),
        },
        '& .MuiInputBase-input': {
          fontSize: { xs: 17, md: 20 },
          fontWeight: 800,
          lineHeight: 1.2,
          px: 0.2,
        },
      }}
    />
  );
};

const UnitListRow = ({
  onOpenUnit,
  row,
}: {
  onOpenUnit: (unit: UnitNode) => void;
  row: VisibleUnitRow;
}) => {
  const staffCount = collectUniqueMembers(row.unit, false).length;
  const contractorCount = collectUniqueMembers(row.unit, true).length;

  return (
    <Box
      role="button"
      tabIndex={0}
      aria-label={`Открыть структуру подразделения ${row.unit.name}`}
      onClick={() => onOpenUnit(row.unit)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onOpenUnit(row.unit);
        }
      }}
      sx={{
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        gap: 0.7,
        minWidth: 0,
        borderRadius: 2.25,
        border: `1px solid ${alpha(hierarchyPageColors.cardBorder, 0.95)}`,
        backgroundColor: '#ffffff',
        boxShadow: hierarchyPageColors.shadow,
        pl: `calc(${row.depth} * 14px + 14px)`,
        pr: 1.2,
        py: 1.1,
        transition: 'border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease',
        '&:hover': {
          borderColor: alpha(hierarchyPageColors.softBlue, 0.4),
          boxShadow: '0 6px 16px rgba(37, 99, 235, 0.10)',
          transform: 'translateY(-1px)',
        },
        '&:focus-visible': {
          outline: `2px solid ${alpha(hierarchyPageColors.softBlue, 0.45)}`,
          outlineOffset: 2,
        },
      }}
    >
      <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="flex-start">
        <Box sx={{ minWidth: 0 }}>
          <Typography sx={{ fontSize: 14.5, fontWeight: 700, lineHeight: 1.25, overflowWrap: 'anywhere' }}>
            {row.unit.name}
          </Typography>
          <Typography sx={{ mt: 0.2, fontSize: 11.5, color: hierarchyPageColors.textSecondary, overflowWrap: 'anywhere' }}>
            {row.pathLabel}
          </Typography>
        </Box>
        <Chip
          size="small"
          icon={<OpenInFullRoundedIcon sx={{ fontSize: '16px !important' }} />}
          label="Схема"
          sx={{ flexShrink: 0 }}
        />
      </Stack>

      <UnitStatRow
        childrenCount={row.unit.children.length}
        contractorCount={contractorCount}
        staffCount={staffCount}
      />
    </Box>
  );
};

export const UnitHierarchyPageView = () => {
  const {
    departments,
    isLoading,
    error,
    selectedDepartmentId,
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
    isSavingUnitNameId,
    submitUnitName,
    deleteDialogState,
    isDeletingUnit,
    openDeleteDialog,
    closeDeleteDialog,
    confirmDeleteUnit,
    findRootUnitForUnit,
    loadTree,
  } = useUnitHierarchyPage();

  const [searchQuery, setSearchQuery] = useState('');
  const deferredSearchQuery = useDeferredValue(searchQuery);

  const normalizedQuery = useMemo(
    () => normalizeSearch(deferredSearchQuery),
    [deferredSearchQuery]
  );

  const filteredDepartmentViews = useMemo<FilteredDepartmentView[]>(
    () => departments
      .map((department) => {
        const filteredDepartment = filterUnitTree(department, normalizedQuery);
        if (!filteredDepartment) {
          return null;
        }

        const totalStaff = collectUniqueMembers(department, false).length;
        const totalContractors = collectUniqueMembers(department, true).length;

        return {
          department,
          filteredDepartment,
          totalUnits: countUnits(department),
          visibleUnits: countUnits(filteredDepartment),
          totalStaff,
          visibleStaff: collectUniqueMembers(filteredDepartment, false),
          totalContractors,
          visibleContractors: collectUniqueMembers(filteredDepartment, true),
        };
      })
      .filter((view): view is FilteredDepartmentView => view !== null),
    [departments, normalizedQuery]
  );

  const selectedDepartmentView = useMemo(
    () => filteredDepartmentViews.find((item) => item.department.unit_id === selectedDepartmentId) ?? filteredDepartmentViews[0] ?? null,
    [filteredDepartmentViews, selectedDepartmentId]
  );

  const visibleUnitRows = useMemo(
    () => (selectedDepartmentView ? buildVisibleUnitRows(selectedDepartmentView.filteredDepartment) : []),
    [selectedDepartmentView]
  );

  const totalDepartmentCount = departments.length;
  const totalUnitCount = useMemo(
    () => departments.reduce((sum, department) => sum + countUnits(department), 0),
    [departments]
  );
  const totalStaffCount = useMemo(
    () => departments.reduce((sum, department) => sum + collectUniqueMembers(department, false).length, 0),
    [departments]
  );
  const totalContractorCount = useMemo(
    () => departments.reduce((sum, department) => sum + collectUniqueMembers(department, true).length, 0),
    [departments]
  );

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
      <Card variant="outlined" sx={sectionCardSx}>
        <CardContent sx={{ p: { xs: 1.25, md: 1.75 }, '&:last-child': { pb: { xs: 1.25, md: 1.75 } } }}>
          <Stack spacing={1.35}>
            <Stack
              direction={{ xs: 'column', lg: 'row' }}
              spacing={1.2}
              justifyContent="space-between"
              alignItems={{ xs: 'stretch', lg: 'center' }}
            >
              <Box sx={{ minWidth: 0 }}>
                <Typography sx={{ fontSize: { xs: 22, md: 26 }, fontWeight: 800, lineHeight: 1.1 }}>
                  Подразделения и состав
                </Typography>
                <Typography sx={{ mt: 0.45, maxWidth: 720, fontSize: 13.5, color: hierarchyPageColors.textSecondary }}>
                  Быстрый просмотр всех подразделений, их листов и состава. Откройте нужную карточку, чтобы увидеть структуру подробнее.
                </Typography>
              </Box>

              {canCreateRootUnit ? (
                <Button
                  variant="contained"
                  startIcon={<ApartmentOutlinedIcon />}
                  onClick={openCreateRootDialog}
                  sx={{ alignSelf: { xs: 'stretch', lg: 'center' }, flexShrink: 0 }}
                >
                  Новое подразделение
                </Button>
              ) : null}
            </Stack>

            <Stack
              direction={{ xs: 'column', xl: 'row' }}
              spacing={1}
              alignItems={{ xs: 'stretch', xl: 'center' }}
              justifyContent="space-between"
            >
              <TextField
                fullWidth
                size="small"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Поиск по подразделению, листу, сотруднику или контрагенту"
                InputProps={{
                  startAdornment: <SearchRoundedIcon sx={{ mr: 0.75, color: hierarchyPageColors.textSecondary }} />,
                }}
                sx={{
                  maxWidth: { xl: 520 },
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: alpha('#ffffff', 0.92),
                  },
                }}
              />

              <Stack direction="row" spacing={0.7} useFlexGap flexWrap="wrap">
                <UnitStatTile color={hierarchyPageColors.softBlue} label="Подразделения" value={filteredDepartmentViews.length || totalDepartmentCount} />
                <UnitStatTile color={hierarchyPageColors.softTeal} label="Сотрудники" value={totalStaffCount} />
                <UnitStatTile color={hierarchyPageColors.softPink} label="Контрагенты" value={totalContractorCount} />
                <UnitStatTile color={hierarchyPageColors.connector} label="Всего листов" value={totalUnitCount} />
              </Stack>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {departments.length === 0 ? (
        <Card variant="outlined" sx={sectionCardSx}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              Пока нет подразделений. Создайте первое корневое подразделение.
            </Typography>
          </CardContent>
        </Card>
      ) : filteredDepartmentViews.length === 0 ? (
        <Card variant="outlined" sx={sectionCardSx}>
          <CardContent>
            <Stack spacing={1.25} alignItems="flex-start">
              <Typography sx={{ fontSize: 15, fontWeight: 700 }}>Ничего не найдено</Typography>
              <Typography variant="body2" color="text.secondary">
                Попробуйте изменить фильтр: поиск работает по названиям, логинам, ролям и именам сотрудников.
              </Typography>
              <Button variant="outlined" onClick={() => setSearchQuery('')}>
                Сбросить фильтр
              </Button>
            </Stack>
          </CardContent>
        </Card>
      ) : (
        <Stack spacing={1.5}>
          {filteredDepartmentViews.map((view) => {
            const { department, filteredDepartment } = view;
            const isExpanded = selectedDepartmentView?.department.unit_id === department.unit_id;

            return (
              <Card
                key={department.unit_id}
                variant="outlined"
                sx={{
                  ...sectionCardSx,
                  borderColor: isExpanded ? alpha(hierarchyPageColors.softBlue, 0.34) : alpha(hierarchyPageColors.canvasBorder, 0.9),
                  boxShadow: isExpanded ? '0 8px 24px rgba(37, 99, 235, 0.08)' : sectionCardSx.boxShadow,
                  overflow: 'hidden',
                }}
              >
                <CardContent sx={{ p: { xs: 1.2, md: 1.6 }, '&:last-child': { pb: { xs: 1.2, md: 1.6 } } }}>
                  <Stack spacing={1.2}>
                    <Stack
                      direction={{ xs: 'column', md: 'row' }}
                      spacing={1}
                      justifyContent="space-between"
                      alignItems={{ xs: 'stretch', md: 'flex-start' }}
                    >
                      <Box sx={{ minWidth: 0, flex: 1 }}>
                        {isExpanded ? (
                          <InlineUnitNameField
                            canEdit={department.actions.canUpdate}
                            isSaving={isSavingUnitNameId === department.unit_id}
                            onSubmit={submitUnitName}
                            unit={department}
                          />
                        ) : (
                          <Typography sx={{ fontSize: { xs: 19, md: 21 }, fontWeight: 800, lineHeight: 1.15, overflowWrap: 'anywhere' }}>
                            {department.name}
                          </Typography>
                        )}

                        <Box sx={{ mt: 0.95 }}>
                          <UnitStatRow
                            childrenCount={department.children.length}
                            contractorCount={view.totalContractors}
                            staffCount={view.totalStaff}
                          />
                        </Box>

                        {normalizedQuery ? (
                          <Typography sx={{ mt: 0.8, fontSize: 12, color: hierarchyPageColors.textSecondary }}>
                            Показано {view.visibleUnits} из {view.totalUnits} листов, {view.visibleStaff.length} из {view.totalStaff} сотрудников
                            и {view.visibleContractors.length} из {view.totalContractors} контрагентов.
                          </Typography>
                        ) : null}
                      </Box>

                      <Stack direction="row" spacing={0.8} useFlexGap flexWrap="wrap" sx={{ flexShrink: 0 }}>
                        <Button
                          size="small"
                          variant={isExpanded ? 'contained' : 'outlined'}
                          onClick={() => setSelectedDepartmentId(department.unit_id)}
                        >
                          {isExpanded ? 'Открыто' : 'Подробнее'}
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<DeviceHubOutlinedIcon sx={{ fontSize: 16 }} />}
                          onClick={() => openUnitEditor(department)}
                        >
                          Схема
                        </Button>
                        {department.actions.canManageMembers ? (
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<HandshakeOutlinedIcon sx={{ fontSize: 16 }} />}
                            onClick={() => openContractorDialog(department)}
                          >
                            Контрагент
                          </Button>
                        ) : null}
                        {department.actions.canCreateChild ? (
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<AddOutlinedIcon sx={{ fontSize: 16 }} />}
                            onClick={() => handleAddUnit(department)}
                          >
                            Добавить лист
                          </Button>
                        ) : null}
                      </Stack>
                    </Stack>

                    {isExpanded ? (
                      <>
                        <Divider />

                        <Box
                          sx={{
                            display: 'grid',
                            gap: 1.35,
                            gridTemplateColumns: { xs: '1fr', xl: 'minmax(0, 1.2fr) minmax(320px, 0.8fr)' },
                            alignItems: 'start',
                          }}
                        >
                          <Box
                            sx={{
                              borderRadius: 3,
                              border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
                              backgroundImage: hierarchyCanvasBackground,
                              p: { xs: 1.1, md: 1.35 },
                              minWidth: 0,
                            }}
                          >
                            <Stack spacing={1.1}>
                              <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="center">
                                <Box sx={{ minWidth: 0 }}>
                                  <Typography sx={{ fontSize: 14.5, fontWeight: 800 }}>Структура подразделения</Typography>
                                  <Typography sx={{ fontSize: 12, color: hierarchyPageColors.textSecondary }}>
                                    Откройте нужный лист, чтобы перейти к полной схеме и управлению составом.
                                  </Typography>
                                </Box>
                                <Chip size="small" label={`${visibleUnitRows.length} листов`} />
                              </Stack>

                              {visibleUnitRows.length === 0 ? (
                                <Box
                                  sx={{
                                    borderRadius: 2.25,
                                    border: `1px dashed ${alpha(hierarchyPageColors.softTeal, 0.42)}`,
                                    backgroundColor: alpha(hierarchyPageColors.softTeal, 0.05),
                                    px: 1.25,
                                    py: 1.2,
                                  }}
                                >
                                  <Typography variant="body2" color="text.secondary">
                                    {filteredDepartment.children.length === 0
                                      ? 'В этом подразделении пока нет вложенных листов.'
                                      : 'После фильтра не осталось видимых листов.'}
                                  </Typography>
                                </Box>
                              ) : (
                                <Stack spacing={0.85} sx={{ maxHeight: { xs: 'none', xl: 520 }, overflowY: 'auto', pr: 0.2 }}>
                                  {visibleUnitRows.map((row) => (
                                    <UnitListRow key={row.unit.unit_id} onOpenUnit={openUnitEditor} row={row} />
                                  ))}
                                </Stack>
                              )}
                            </Stack>
                          </Box>

                          <Stack spacing={1.1} sx={{ minWidth: 0 }}>
                            <Card variant="outlined" sx={sectionCardSx}>
                              <CardContent sx={{ p: 1.25, '&:last-child': { pb: 1.25 } }}>
                                <Box sx={{ maxHeight: { xs: 'none', xl: 520 }, overflowY: 'auto', pr: 0.2 }}>
                                  <PeopleTree
                                    emptyLabel="Сотрудников пока нет."
                                    members={view.visibleStaff}
                                    title="Сотрудники подразделения"
                                  />
                                </Box>
                              </CardContent>
                            </Card>

                            <Card variant="outlined" sx={sectionCardSx}>
                              <CardContent sx={{ p: 1.25, '&:last-child': { pb: 1.25 } }}>
                                <Box sx={{ maxHeight: { xs: 'none', xl: 300 }, overflowY: 'auto', pr: 0.2 }}>
                                  <PeopleFlatList
                                    emptyLabel="Контрагентов пока нет."
                                    members={view.visibleContractors}
                                    onRemove={department.actions.canManageMembers ? (member) => {
                                      void removeContractorFromUnit(department, member);
                                    } : undefined}
                                    title="Контрагенты подразделения"
                                  />
                                </Box>
                              </CardContent>
                            </Card>
                          </Stack>
                        </Box>
                      </>
                    ) : null}
                  </Stack>
                </CardContent>
              </Card>
            );
          })}
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
                        Подразделение {editorDepartment?.name ?? 'Без названия'}
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
              <Box sx={{ display: 'grid', gap: 1.6, gridTemplateColumns: { xs: '1fr', lg: 'minmax(0, 1fr) minmax(0, 360px)' }, mt: 1 }}>
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
                              <InlineUnitNameField
                                canEdit={canEditActiveUnit}
                                isSaving={isSavingUnitNameId === activeUnitDetails.unit_id}
                                onSubmit={submitUnitName}
                                unit={activeUnitDetails}
                              />
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
                          onMove={activeUnitDetails.actions.canManageMembers ? (member) => openMoveMemberDialog(activeUnitDetails, member) : undefined}
                          onRemove={activeUnitDetails.actions.canManageMembers ? (member) => {
                            void removeMemberFromUnit(activeUnitDetails, member);
                          } : undefined}
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
                        Выберите лист на схеме, чтобы открыть состав и статистику.
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
