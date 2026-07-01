import ApartmentOutlinedIcon from '@mui/icons-material/ApartmentOutlined';
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import GroupAddOutlinedIcon from '@mui/icons-material/GroupAddOutlined';
import HandshakeOutlinedIcon from '@mui/icons-material/HandshakeOutlined';
import LanOutlinedIcon from '@mui/icons-material/LanOutlined';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  IconButton,
  InputBase,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useDeferredValue, useEffect, useMemo, useState } from 'react';
import { useSetPageBreadcrumbActions, useSetPageBreadcrumbItems } from '@app/layouts/PageBreadcrumbActions';
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
  orgNodeCardSx,
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

type OverviewUnitCard = {
  department: UnitNode;
  filteredUnit: UnitNode;
  totalContractors: number;
  totalStaff: number;
  totalUnits: number;
  visibleContractors: UnitMember[];
  visibleStaff: UnitMember[];
  visibleUnits: number;
  unit: UnitNode;
};

type OverviewMemberView = 'staff' | 'contractors';

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
      ? 'Создать дочернее объединение'
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
              renderInput={(params) => <TextField {...params} label="Родительское объединение" />}
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

const buildOverviewUnitCards = (department: UnitNode, normalizedQuery: string): OverviewUnitCard[] => {
  const departmentMatches = normalizedQuery
    ? department.name.toLocaleLowerCase('ru').includes(normalizedQuery)
    : true;

  return department.children
    .map((unit) => {
      const filteredUnit = !normalizedQuery || departmentMatches
        ? unit
        : filterUnitTree(unit, normalizedQuery);

      if (!filteredUnit) {
        return null;
      }

      return {
        department,
        filteredUnit,
        totalContractors: collectUniqueMembers(unit, true).length,
        totalStaff: collectUniqueMembers(unit, false).length,
        totalUnits: countUnits(unit),
        visibleContractors: collectUniqueMembers(filteredUnit, true),
        visibleStaff: collectUniqueMembers(filteredUnit, false),
        visibleUnits: countUnits(filteredUnit),
        unit,
      };
    })
    .filter((card): card is OverviewUnitCard => card !== null);
};

const sumVisibleMembers = (cards: OverviewUnitCard[], key: 'visibleStaff' | 'visibleContractors') =>
  cards.reduce((sum, card) => sum + card[key].length, 0);

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
  staffCount,
}: {
  childrenCount?: number | undefined;
  staffCount: number;
}) => (
  <Stack direction="row" spacing={0.7} useFlexGap flexWrap="wrap" sx={{ minWidth: 0 }}>
    <UnitStatTile color={hierarchyPageColors.softTeal} label="Сотрудники" value={staffCount} />
    {childrenCount !== undefined ? (
      <UnitStatTile color={hierarchyPageColors.softBlue} label="Группы" value={childrenCount} />
    ) : null}
  </Stack>
);

const compactOverviewActionButtonSx = {
  ...outlinedIconButtonSx,
  width: 36,
  height: 36,
} as const;

const CompactUnitActions = ({
  canManageMembers,
  onManageContractors,
  onOpenSchema,
  showContractorsButton = true,
  size = 'small',
  unitName,
}: {
  canManageMembers: boolean;
  onManageContractors: () => void;
  onOpenSchema: () => void;
  showContractorsButton?: boolean;
  size?: 'small' | 'medium';
  unitName: string;
}) => {
  const isSmall = size === 'small';

  return (
    <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap" alignItems="center">
      <Button
        size={size}
        variant="outlined"
        startIcon={<LanOutlinedIcon sx={{ fontSize: 16 }} />}
        onClick={onOpenSchema}
        sx={{ minHeight: isSmall ? 38 : 42, borderRadius: isSmall ? 1.5 : 1.75, px: isSmall ? 1.6 : 2 }}
      >
        Схема
      </Button>
      {showContractorsButton && canManageMembers ? (
        <Tooltip title="Контрагенты">
          <IconButton
            size="small"
            aria-label={`Открыть контрагентов объединения ${unitName}`}
            onClick={onManageContractors}
            sx={compactOverviewActionButtonSx}
          >
            <HandshakeOutlinedIcon sx={{ fontSize: 17 }} />
          </IconButton>
        </Tooltip>
      ) : null}
    </Stack>
  );
};

const OverviewMemberViewToggle = ({
  contractorCount,
  staffCount,
  value,
  onChange,
}: {
  contractorCount: number;
  staffCount: number;
  value: OverviewMemberView;
  onChange: (nextValue: OverviewMemberView) => void;
}) => {
  const options: Array<{ color: string; count: number; label: string; value: OverviewMemberView }> = [
    {
      color: hierarchyPageColors.softTeal,
      count: staffCount,
      label: 'Сотрудники',
      value: 'staff',
    },
    {
      color: hierarchyPageColors.softPink,
      count: contractorCount,
      label: 'Контрагенты',
      value: 'contractors',
    },
  ];

  return (
    <Box
      role="tablist"
      aria-label="Переключение списка участников"
      sx={{
        display: 'inline-flex',
        alignSelf: 'flex-start',
        gap: 0.45,
        p: 0.45,
        borderRadius: 2,
        border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.92)}`,
        backgroundColor: alpha(hierarchyPageColors.canvas, 0.88),
      }}
    >
      {options.map((option) => {
        const isActive = option.value === value;

        return (
          <Box
            key={option.value}
            component="button"
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(option.value)}
            sx={{
              appearance: 'none',
              border: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 0.8,
              borderRadius: 1.5,
              backgroundColor: isActive ? '#ffffff' : 'transparent',
              boxShadow: isActive ? '0 1px 2px rgba(15, 23, 42, 0.06)' : 'none',
              color: isActive ? hierarchyPageColors.textPrimary : hierarchyPageColors.textSecondary,
              cursor: 'pointer',
              font: 'inherit',
              px: 1.15,
              py: 0.8,
              transition: 'background-color 0.16s ease, color 0.16s ease, box-shadow 0.16s ease',
            }}
          >
            <Typography sx={{ fontSize: 13.5, fontWeight: 800, lineHeight: 1, color: 'inherit' }}>
              {option.label}
            </Typography>
            <Box
              component="span"
              sx={{
                minWidth: 22,
                borderRadius: 999,
                backgroundColor: alpha(option.color, isActive ? 0.16 : 0.1),
                color: isActive ? option.color : hierarchyPageColors.textSecondary,
                px: 0.7,
                py: 0.2,
                fontSize: 11,
                fontWeight: 800,
                lineHeight: 1,
                textAlign: 'center',
              }}
            >
              {option.count}
            </Box>
          </Box>
        );
      })}
    </Box>
  );
};

void OverviewMemberViewToggle;

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
  const unitNameLabel = unit.id_parent === null ? 'Название подразделения' : 'Название группы';

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
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        minHeight: { xs: 42, md: 46 },
        px: { xs: 1.1, md: 1.25 },
        borderRadius: 2,
        border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.9)}`,
        backgroundColor: '#ffffff',
        '&:focus-within': {
          borderColor: hierarchyPageColors.softBlue,
        },
      }}
    >
      <InputBase
        fullWidth
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
        placeholder={unitNameLabel}
        inputProps={{ 'aria-label': `${unitNameLabel} ${unit.name}` }}
        sx={{
          flex: 1,
          minWidth: 0,
          color: hierarchyPageColors.textPrimary,
          '& .MuiInputBase-input': {
            px: 0,
            py: 0,
            fontSize: { xs: 17, md: 20 },
            fontWeight: 800,
            lineHeight: 1.2,
            letterSpacing: '-0.015em',
          },
          '& .MuiInputBase-input::placeholder': {
            color: alpha(hierarchyPageColors.textSecondary, 0.82),
            opacity: 1,
          },
        }}
      />
      {isSaving ? <CircularProgress size={15} sx={{ flexShrink: 0, color: hierarchyPageColors.softBlue }} /> : null}
    </Box>
  );
};

const UnitListRow = ({
  card,
  isSelected,
  onOpenUnit,
  onSelect,
  variant = 'card',
}: {
  card: OverviewUnitCard;
  isSelected: boolean;
  onOpenUnit: (unit: UnitNode) => void;
  onSelect: (unitId: number) => void;
  variant?: 'card' | 'list';
}) => {
  const isList = variant === 'list';

  const baseInteractionSx = {
    cursor: 'pointer',
    minWidth: 0,
    width: '100%',
    maxWidth: '100%',
    border: `1px solid ${isSelected ? alpha(hierarchyPageColors.softBlue, 0.4) : alpha(hierarchyPageColors.canvasBorder, 0.98)}`,
    backgroundColor: isSelected ? alpha(hierarchyPageColors.softBlue, 0.05) : '#ffffff',
    transition: 'border-color 0.16s ease, background-color 0.16s ease',
    '&:hover': {
      borderColor: alpha(hierarchyPageColors.softBlue, 0.4),
    },
    '&:focus-visible': {
      outline: `2px solid ${alpha(hierarchyPageColors.softBlue, 0.45)}`,
      outlineOffset: 2,
    },
  } as const;

  const openButton = (
    <IconButton
      size="small"
      aria-label={`Открыть схему объединения ${card.unit.name}`}
      onClick={(event) => {
        event.stopPropagation();
        onOpenUnit(card.unit);
      }}
      sx={{
        ...outlinedIconButtonSx,
        flexShrink: 0,
      }}
    >
      <LanOutlinedIcon sx={{ fontSize: 18 }} />
    </IconButton>
  );

  if (isList) {
    return (
      <Box
        role="button"
        tabIndex={0}
        aria-label={`Выбрать объединение ${card.unit.name}`}
        onClick={() => onSelect(card.unit.unit_id)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            onSelect(card.unit.unit_id);
          }
        }}
        sx={{
          ...baseInteractionSx,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          borderRadius: 1.5,
          px: 1.1,
          py: 0.85,
        }}
      >
        <Typography
          sx={{ flex: 1, minWidth: 0, fontSize: 13.5, fontWeight: 700, lineHeight: 1.25, color: hierarchyPageColors.textPrimary, overflowWrap: 'anywhere' }}
        >
          {card.unit.name}
        </Typography>
        <UnitStatRow
          childrenCount={card.unit.children.length}
          staffCount={card.totalStaff}
        />
        {openButton}
      </Box>
    );
  }

  return (
    <Box
      role="button"
      tabIndex={0}
      aria-label={`Выбрать объединение ${card.unit.name}`}
      onClick={() => onSelect(card.unit.unit_id)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onSelect(card.unit.unit_id);
        }
      }}
      sx={{
        ...orgNodeCardSx,
        ...baseInteractionSx,
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        boxShadow: '0 1px 2px rgba(15, 23, 42, 0.03)',
      }}
    >
      <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="center">
        <Box sx={{ minWidth: 0 }}>
          <Typography sx={{ fontSize: 15, fontWeight: 700, lineHeight: 1.24, color: hierarchyPageColors.textPrimary, overflowWrap: 'anywhere' }}>
            {card.unit.name}
          </Typography>
          <Typography sx={{ mt: 0.2, fontSize: 11.5, color: hierarchyPageColors.textSecondary, overflowWrap: 'anywhere' }}>
            {card.department.name}
          </Typography>
        </Box>

        <Box sx={{ mr: -0.35 }}>{openButton}</Box>
      </Stack>

      <UnitStatRow
        childrenCount={card.unit.children.length}
        staffCount={card.totalStaff}
      />
    </Box>
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
    canManageUnitMembers,
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
    unassignedUsers,
    isLoadingUnassignedUsers,
    assignMemberState,
    isAssigningMember,
    assignUnitOptions,
    openAssignMemberDialog,
    closeAssignMemberDialog,
    submitAssignMember,
    setAssignMemberState,
  } = useUnitHierarchyPage();

  const [departmentScope, setDepartmentScope] = useState<'all' | number>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOverviewUnitId, setSelectedOverviewUnitId] = useState<number | null>(null);
  const [selectedOverviewMemberView, setSelectedOverviewMemberView] = useState<OverviewMemberView>('staff');
  const deferredSearchQuery = useDeferredValue(searchQuery);

  void setSelectedOverviewMemberView;

  const normalizedQuery = useMemo(
    () => normalizeSearch(deferredSearchQuery),
    [deferredSearchQuery]
  );

  const departmentOptions = useMemo(
    () => [
      { unitId: 'all', label: 'Все подразделения' },
      ...departments.map((department) => ({
        unitId: String(department.unit_id),
        label: department.name,
      })),
    ],
    [departments]
  );

  const scopedDepartments = useMemo(
    () => (departmentScope === 'all'
      ? departments
      : departments.filter((department) => department.unit_id === departmentScope)),
    [departmentScope, departments]
  );

  const scopedDepartment = useMemo(
    () => (departmentScope === 'all' ? null : scopedDepartments[0] ?? null),
    [departmentScope, scopedDepartments]
  );

  const selectedDepartmentView = useMemo<FilteredDepartmentView | null>(
    () => {
      if (!scopedDepartment) {
        return null;
      }

      const filteredDepartment = filterUnitTree(scopedDepartment, normalizedQuery);
      if (!filteredDepartment) {
        return null;
      }

      const totalStaff = collectUniqueMembers(scopedDepartment, false).length;
      const totalContractors = collectUniqueMembers(scopedDepartment, true).length;

      return {
        department: scopedDepartment,
        filteredDepartment,
        totalUnits: countUnits(scopedDepartment),
        visibleUnits: countUnits(filteredDepartment),
        totalStaff,
        visibleStaff: collectUniqueMembers(filteredDepartment, false),
        totalContractors,
        visibleContractors: collectUniqueMembers(filteredDepartment, true),
      };
    },
    [normalizedQuery, scopedDepartment]
  );

  const overviewCards = useMemo(
    () => scopedDepartments.flatMap((department) => buildOverviewUnitCards(department, normalizedQuery)),
    [normalizedQuery, scopedDepartments]
  );

  const selectedOverviewCard = useMemo(
    () => overviewCards.find((card) => card.unit.unit_id === selectedOverviewUnitId) ?? overviewCards[0] ?? null,
    [overviewCards, selectedOverviewUnitId]
  );

  const overviewGroups = useMemo(() => {
    const groups: { department: UnitNode; cards: OverviewUnitCard[] }[] = [];
    const indexByDepartment = new Map<number, number>();
    overviewCards.forEach((card) => {
      const departmentId = card.department.unit_id;
      let groupIndex = indexByDepartment.get(departmentId);
      if (groupIndex === undefined) {
        groupIndex = groups.length;
        indexByDepartment.set(departmentId, groupIndex);
        groups.push({ department: card.department, cards: [] });
      }
      groups[groupIndex]!.cards.push(card);
    });
    return groups;
  }, [overviewCards]);

  const overviewScopeSummary = useMemo(() => {
    if (departmentScope === 'all') {
      return {
        leafCount: overviewCards.length,
        staffCount: scopedDepartments.reduce((sum, department) => sum + collectUniqueMembers(department, false).length, 0),
        title: 'Все подразделения',
      };
    }

    return {
      leafCount: scopedDepartment?.children.length ?? 0,
      staffCount: selectedDepartmentView?.totalStaff ?? 0,
      title: scopedDepartment?.name ?? 'Подразделение',
    };
  }, [departmentScope, overviewCards.length, scopedDepartment, scopedDepartments, selectedDepartmentView]);

  const selectedOverviewVisibleMembers = selectedOverviewMemberView === 'staff'
    ? selectedOverviewCard?.visibleStaff ?? []
    : selectedOverviewCard?.visibleContractors ?? [];

  useEffect(() => {
    if (departmentScope !== 'all' && !departments.some((department) => department.unit_id === departmentScope)) {
      setDepartmentScope('all');
    }
  }, [departmentScope, departments]);

  useEffect(() => {
    if (overviewCards.length === 0) {
      setSelectedOverviewUnitId(null);
      return;
    }
    if (selectedOverviewUnitId === null || !overviewCards.some((card) => card.unit.unit_id === selectedOverviewUnitId)) {
      setSelectedOverviewUnitId(overviewCards[0]!.unit.unit_id);
    }
  }, [overviewCards, selectedOverviewUnitId]);

  const selectedUser = availableUsers.find((user) => user.user_id === memberDialogState.selectedUserId) ?? null;
  const selectedMoveTarget = moveUnitOptions.find((option) => option.unitId === moveMemberState?.targetUnitId) ?? null;
  const selectedAssignTarget = assignUnitOptions.find((option) => option.unitId === assignMemberState?.targetUnitId) ?? null;

  const detailStaff = useMemo(
    () => (activeUnitDetails?.members ?? []).filter((member) => member.role_id !== ROLE.CONTRACTOR),
    [activeUnitDetails]
  );
  const detailContractors = useMemo(
    () => (activeUnitDetails?.members ?? []).filter((member) => member.role_id === ROLE.CONTRACTOR),
    [activeUnitDetails]
  );

  const unassignedMembers = useMemo<UnitMember[]>(
    () => (unassignedUsers ?? [])
      .map((user) => ({
        user_id: user.user_id,
        full_name: user.full_name,
        role_id: user.role_id,
        role_name: user.role_name,
        status: user.status,
        id_parent_user: null,
      }))
      .filter((member) => matchesMemberQuery(member, normalizedQuery)),
    [normalizedQuery, unassignedUsers]
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

  const handleSelectDepartmentScope = (departmentId: number) => {
    setDepartmentScope(departmentId);
    setSelectedDepartmentId(departmentId);
  };

  const breadcrumbActions = useMemo(() => {
    if (isLoading || error) {
      return null;
    }

    return (
      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={1}
        alignItems={{ xs: 'stretch', md: 'center' }}
        sx={{ width: { xs: '100%', md: 'auto' }, flex: { md: 1 }, justifyContent: 'flex-end' }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            width: { xs: '100%', md: 'auto' },
            flex: { md: '1 1 auto' },
            minWidth: { md: 320 },
            maxWidth: { md: 560 },
            minHeight: 44,
            borderRadius: 1.5,
            border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
            backgroundColor: alpha('#ffffff', 0.96),
            boxShadow: '0 1px 2px rgba(15, 23, 42, 0.03)',
            px: 1,
          }}
        >
          <FormControl variant="standard" sx={{ minWidth: { xs: 120, sm: 170 }, maxWidth: { xs: 150, sm: 200 }, flexShrink: 0 }}>
            <Select
              disableUnderline
              value={departmentScope === 'all' ? 'all' : String(departmentScope)}
              onChange={(event) => {
                const nextValue = event.target.value;
                if (nextValue === 'all') {
                  setDepartmentScope('all');
                  return;
                }
                const nextDepartmentId = Number(nextValue);
                setDepartmentScope(nextDepartmentId);
                setSelectedDepartmentId(nextDepartmentId);
              }}
              displayEmpty
              inputProps={{ 'aria-label': 'Подразделение для просмотра' }}
              sx={{
                minHeight: 40,
                fontSize: 14,
                fontWeight: 700,
                color: hierarchyPageColors.textPrimary,
                '& .MuiSelect-select': {
                  display: 'flex',
                  alignItems: 'center',
                  py: 0,
                  pl: 0,
                  pr: 3.25,
                },
              }}
            >
              {departmentOptions.map((option) => (
                <MenuItem key={option.unitId} value={String(option.unitId)}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Divider orientation="vertical" flexItem sx={{ mx: 1, my: 0.75 }} />

          <SearchRoundedIcon sx={{ mr: 0.85, color: hierarchyPageColors.textSecondary, flexShrink: 0 }} />

          <InputBase
            fullWidth
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Поиск по подразделению, группе, сотруднику или контрагенту"
            inputProps={{ 'aria-label': 'Поиск по иерархии' }}
            sx={{
              flex: 1,
              minWidth: 0,
              fontSize: 15,
              color: hierarchyPageColors.textPrimary,
            }}
          />
        </Box>

        {canCreateRootUnit ? (
          <Button
            variant="contained"
            startIcon={<ApartmentOutlinedIcon />}
            onClick={openCreateRootDialog}
            sx={{
              minHeight: 44,
              borderRadius: 1.5,
              flexShrink: 0,
              px: 2,
              fontSize: 14,
              fontWeight: 700,
              whiteSpace: 'nowrap',
            }}
          >
            Новое подразделение
          </Button>
        ) : null}
      </Stack>
    );
  }, [
    canCreateRootUnit,
    departmentOptions,
    departmentScope,
    error,
    isLoading,
    openCreateRootDialog,
    searchQuery,
    setDepartmentScope,
    setSearchQuery,
    setSelectedDepartmentId,
  ]);

  const breadcrumbItems = useMemo(
    () => (scopedDepartment
      ? [
          {
            key: 'hierarchy-root',
            label: 'Иерархия',
            onClick: () => setDepartmentScope('all'),
          },
          {
            key: `hierarchy-department-${scopedDepartment.unit_id}`,
            label: scopedDepartment.name,
          },
        ]
      : []),
    [scopedDepartment]
  );

  useSetPageBreadcrumbActions(breadcrumbActions);
  useSetPageBreadcrumbItems(breadcrumbItems);

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
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, pb: 1 }}>
      {departments.length === 0 ? (
        <Card variant="outlined" sx={sectionCardSx}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              Пока нет подразделений. Создайте первое корневое подразделение.
            </Typography>
          </CardContent>
        </Card>
      ) : overviewCards.length === 0 ? (
        <Card variant="outlined" sx={sectionCardSx}>
          <CardContent>
            <Stack spacing={1.25} alignItems="flex-start">
              <Typography sx={{ fontSize: 15, fontWeight: 700 }}>Ничего не найдено</Typography>
              <Typography variant="body2" color="text.secondary">
                {departmentScope === 'all'
                  ? 'По выбранному фильтру не найдено объединений второго уровня. Попробуйте изменить поиск или выбрать конкретное подразделение.'
                  : `В подразделении «${scopedDepartment?.name ?? 'Без названия'}» не найдено объединений второго уровня. Попробуйте изменить поиск.`}
              </Typography>
              <Button variant="outlined" onClick={() => setSearchQuery('')}>
                Сбросить фильтр
              </Button>
            </Stack>
          </CardContent>
        </Card>
      ) : (
        <Stack spacing={1.25}>
          <Card
            variant="outlined"
            sx={{
              ...sectionCardSx,
              borderRadius: 2.5,
              overflow: 'hidden',
              borderColor: alpha(hierarchyPageColors.canvasBorder, 0.95),
            }}
          >
            <CardContent sx={{ p: { xs: 1.25, md: 1.7 }, '&:last-child': { pb: { xs: 1.25, md: 1.7 } } }}>
              <Stack spacing={1.2}>
                <Stack
                  direction={{ xs: 'column', xl: 'row' }}
                  spacing={1.2}
                  justifyContent="space-between"
                  alignItems={{ xs: 'stretch', xl: 'flex-start' }}
                >
                  <Box sx={{ minWidth: 0, flex: 1 }}>
                    {departmentScope === 'all' || !selectedDepartmentView ? (
                      <Typography sx={{ fontSize: { xs: 18, md: 21 }, fontWeight: 800, lineHeight: 1.2, overflowWrap: 'anywhere' }}>
                        {overviewScopeSummary.title}
                      </Typography>
                    ) : (
                      <InlineUnitNameField
                        canEdit={selectedDepartmentView.department.actions.canUpdate}
                        isSaving={isSavingUnitNameId === selectedDepartmentView.department.unit_id}
                        onSubmit={submitUnitName}
                        unit={selectedDepartmentView.department}
                      />
                    )}

                    <Stack direction="row" spacing={0.7} useFlexGap flexWrap="wrap" sx={{ mt: 1.1 }}>
                      <UnitStatTile color={hierarchyPageColors.softTeal} label="Сотрудники" value={overviewScopeSummary.staffCount} />
                      <UnitStatTile color={hierarchyPageColors.softBlue} label="Объединения" value={overviewScopeSummary.leafCount} />
                    </Stack>
                  </Box>

                  {departmentScope !== 'all' && selectedDepartmentView ? (
                    <CompactUnitActions
                      canManageMembers={selectedDepartmentView.department.actions.canManageMembers}
                      onManageContractors={() => openContractorDialog(selectedDepartmentView.department)}
                      onOpenSchema={() => openUnitEditor(selectedDepartmentView.department)}
                      showContractorsButton
                      size="medium"
                      unitName={selectedDepartmentView.department.name}
                    />
                  ) : null}
                </Stack>

                <Divider />

                <Box
                  sx={{
                    display: 'grid',
                    gap: 1.5,
                    gridTemplateColumns: { xs: '1fr', xl: 'minmax(0, 1.58fr) minmax(360px, 1fr)' },
                    alignItems: 'start',
                  }}
                >
                  <Box
                    sx={{
                      minWidth: 0,
                      alignSelf: 'stretch',
                      borderRadius: 2,
                      border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.92)}`,
                      backgroundColor: '#ffffff',
                      p: { xs: 1.05, md: 1.35 },
                    }}
                  >
                    <Stack spacing={1}>
                      <Box sx={{ minWidth: 0 }}>
                        <Typography sx={{ fontSize: 14.5, fontWeight: 800 }}>
                          {departmentScope === 'all' ? 'Объединения по всем подразделениям' : 'Объединения подразделения'}
                        </Typography>
                        <Typography sx={{ fontSize: 12, color: hierarchyPageColors.textSecondary }}>
                          Показаны только объединения второго уровня: первые дети выбранного подразделения.
                        </Typography>
                      </Box>

                      <Box
                        sx={{
                          maxHeight: { xs: 'none', xl: 420 },
                          overflowY: 'auto',
                          pr: 0.2,
                        }}
                      >
                        {departmentScope === 'all' ? (
                          <Stack spacing={1.4}>
                            {overviewGroups.map((group) => (
                              <Box key={group.department.unit_id} sx={{ minWidth: 0 }}>
                                <Box
                                  role="button"
                                  tabIndex={0}
                                  aria-label={`Открыть подразделение ${group.department.name}`}
                                  onClick={() => handleSelectDepartmentScope(group.department.unit_id)}
                                  onKeyDown={(event) => {
                                    if (event.key === 'Enter' || event.key === ' ') {
                                      event.preventDefault();
                                      handleSelectDepartmentScope(group.department.unit_id);
                                    }
                                  }}
                                  sx={{
                                    display: 'flex',
                                    alignItems: 'baseline',
                                    gap: 0.85,
                                    cursor: 'pointer',
                                    borderRadius: 1,
                                    px: 0.4,
                                    py: 0.35,
                                    transition: 'background-color 0.16s ease',
                                    '&:hover': { backgroundColor: alpha(hierarchyPageColors.softBlue, 0.06) },
                                    '&:focus-visible': {
                                      outline: `2px solid ${alpha(hierarchyPageColors.softBlue, 0.45)}`,
                                      outlineOffset: 2,
                                    },
                                  }}
                                >
                                  <Typography sx={{ fontSize: 14.5, fontWeight: 800, color: hierarchyPageColors.textPrimary, overflowWrap: 'anywhere' }}>
                                    {group.department.name}
                                  </Typography>
                                  <Typography sx={{ fontSize: 11.5, fontWeight: 600, color: hierarchyPageColors.softBlue, whiteSpace: 'nowrap' }}>
                                    {group.cards.length} объед.
                                  </Typography>
                                </Box>
                                <Stack spacing={0.75} sx={{ mt: 0.6, pl: 0.4 }}>
                                  {group.cards.map((card) => (
                                    <UnitListRow
                                      key={card.unit.unit_id}
                                      variant="list"
                                      card={card}
                                      isSelected={selectedOverviewCard?.unit.unit_id === card.unit.unit_id}
                                      onOpenUnit={openUnitEditor}
                                      onSelect={setSelectedOverviewUnitId}
                                    />
                                  ))}
                                </Stack>
                              </Box>
                            ))}
                          </Stack>
                        ) : (
                          <Box
                            sx={{
                              display: 'grid',
                              gap: 1,
                              gridTemplateColumns: { xs: '1fr', md: 'repeat(auto-fit, minmax(312px, 1fr))' },
                              alignItems: 'start',
                            }}
                          >
                            {overviewCards.map((card) => (
                              <UnitListRow
                                key={card.unit.unit_id}
                                variant="card"
                                card={card}
                                isSelected={selectedOverviewCard?.unit.unit_id === card.unit.unit_id}
                                onOpenUnit={openUnitEditor}
                                onSelect={setSelectedOverviewUnitId}
                              />
                            ))}
                          </Box>
                        )}
                      </Box>
                    </Stack>
                  </Box>

                  <Stack spacing={1} sx={{ minWidth: 0 }}>
                    <Card variant="outlined" sx={{ ...sectionCardSx, overflow: 'hidden' }}>
                      <CardContent sx={{ p: 1.1, '&:last-child': { pb: 1.1 } }}>
                        {selectedOverviewCard ? (
                          <Stack spacing={1.15}>
                            <Stack
                              direction={{ xs: 'column', sm: 'row' }}
                              spacing={1}
                              justifyContent="space-between"
                              alignItems={{ xs: 'stretch', sm: 'flex-start' }}
                            >
                              <Box sx={{ minWidth: 0, flex: 1 }}>
                                <Typography sx={{ fontSize: 14.5, fontWeight: 800, overflowWrap: 'anywhere' }}>
                                  {selectedOverviewCard.unit.name}
                                </Typography>
                                <Typography sx={{ fontSize: 12, color: hierarchyPageColors.textSecondary, overflowWrap: 'anywhere' }}>
                                  {selectedOverviewCard.department.name}
                                </Typography>
                              </Box>
                              <CompactUnitActions
                                canManageMembers={selectedOverviewCard.unit.actions.canManageMembers}
                                onManageContractors={() => openContractorDialog(selectedOverviewCard.unit)}
                                onOpenSchema={() => openUnitEditor(selectedOverviewCard.unit)}
                                showContractorsButton={false}
                                unitName={selectedOverviewCard.unit.name}
                              />
                            </Stack>

                            <UnitStatRow
                              childrenCount={selectedOverviewCard.unit.children.length}
                              staffCount={selectedOverviewCard.totalStaff}
                            />
                            <Divider />

                            <Box
                              sx={{
                                maxHeight: { xs: 'none', xl: 488 },
                                overflowY: 'auto',
                                pr: 0.2,
                              }}
                            >
                              {selectedOverviewMemberView === 'staff' ? (
                                <PeopleTree
                                  emptyLabel="Сотрудников пока нет."
                                  hideHeader
                                  members={selectedOverviewVisibleMembers}
                                  title="Сотрудники объединения"
                                />
                              ) : (
                                <PeopleFlatList
                                  emptyLabel="Контрагентов пока нет."
                                  hideHeader
                                  members={selectedOverviewVisibleMembers}
                                  title="Контрагенты объединения"
                                />
                              )}
                            </Box>
                          </Stack>
                        ) : null}
                      </CardContent>
                    </Card>
                  </Stack>
                </Box>

                {normalizedQuery ? (
                  <Typography sx={{ fontSize: 12, color: hierarchyPageColors.textSecondary }}>
                    Показано {overviewCards.length} объединений, {overviewCards.reduce((sum, card) => sum + card.visibleUnits, 0)} видимых групп, {sumVisibleMembers(overviewCards, 'visibleStaff')} сотрудников и {sumVisibleMembers(overviewCards, 'visibleContractors')} контрагентов.
                  </Typography>
                ) : null}
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      )}

      {departments.length > 0 && canManageUnitMembers ? (
        <Card
          variant="outlined"
          sx={{
            ...sectionCardSx,
            borderRadius: 2.5,
            borderColor: alpha(hierarchyPageColors.canvasBorder, 0.95),
          }}
        >
          <CardContent sx={{ p: { xs: 1.25, md: 1.7 }, '&:last-child': { pb: { xs: 1.25, md: 1.7 } } }}>
            <Stack spacing={1.2}>
              <Stack
                direction="row"
                spacing={1}
                justifyContent="space-between"
                alignItems="center"
                useFlexGap
                flexWrap="wrap"
              >
                <Box sx={{ minWidth: 0 }}>
                  <Typography sx={{ fontSize: { xs: 16, md: 18 }, fontWeight: 800, lineHeight: 1.2 }}>
                    Нераспределённые сотрудники
                  </Typography>
                  <Typography sx={{ fontSize: 12, color: hierarchyPageColors.textSecondary }}>
                    Активные сотрудники, не закреплённые ни за одним объединением. Нажмите на кнопку рядом с сотрудником, чтобы быстро определить его в нужное объединение.
                  </Typography>
                </Box>
                <UnitStatTile
                  color={hierarchyPageColors.softPink}
                  label="Сотрудники"
                  value={unassignedMembers.length}
                />
              </Stack>

              <Divider />

              {isLoadingUnassignedUsers && unassignedMembers.length === 0 ? (
                <Stack direction="row" spacing={1} alignItems="center" sx={{ py: 0.5 }}>
                  <CircularProgress size={16} />
                  <Typography variant="body2" color="text.secondary">
                    Загрузка списка...
                  </Typography>
                </Stack>
              ) : (
                <Box sx={{ maxHeight: { xs: 'none', md: 360 }, overflowY: 'auto', pr: 0.2 }}>
                  <PeopleFlatList
                    emptyLabel={normalizedQuery
                      ? 'По заданному поиску нераспределённых сотрудников не найдено.'
                      : 'Все сотрудники закреплены за подразделениями.'}
                    hideHeader
                    members={unassignedMembers}
                    onAssign={(member) => openAssignMemberDialog(member)}
                    title="Нераспределённые сотрудники"
                  />
                </Box>
              )}
            </Stack>
          </CardContent>
        </Card>
      ) : null}

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
                    onDelete={openDeleteDialog}
                    onOpenCreateChildDialog={openCreateChildDialog}
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
                          staffCount={detailStaff.length}
                        />

                        <Divider />

                        <PeopleTree
                          emptyLabel="В этой группе пока нет сотрудников."
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
                        Выберите объединение на схеме, чтобы открыть состав и статистику.
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
        <DialogTitle>Добавить сотрудника в объединение</DialogTitle>
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
            noOptionsText={isLoadingUsers ? 'Загружаем сотрудников...' : 'Сотрудники не найдены'}
            loadingText="Загружаем сотрудников..."
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
        <DialogTitle>Перенести сотрудника в другое объединение</DialogTitle>
        <DialogContent dividers>
          <Autocomplete
            options={moveUnitOptions}
            value={selectedMoveTarget}
            onChange={(_event, value) => {
              setMoveMemberState((current) => current ? { ...current, targetUnitId: value?.unitId ?? null } : current);
            }}
            getOptionLabel={(option) => option.label}
            isOptionEqualToValue={(option, value) => option.unitId === value.unitId}
            renderInput={(params) => <TextField {...params} label="Целевое объединение" />}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeMoveMemberDialog}>Отмена</Button>
          <Button variant="contained" disabled={isMovingMember || !moveMemberState?.targetUnitId} onClick={() => void submitMoveMember()}>
            {isMovingMember ? 'Переносим...' : 'Перенести'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(assignMemberState)} onClose={closeAssignMemberDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {assignMemberState?.user.full_name?.trim()
            ? `Определить сотрудника «${assignMemberState.user.full_name}» в объединение`
            : 'Определить сотрудника в объединение'}
        </DialogTitle>
        <DialogContent dividers>
          <Autocomplete
            options={assignUnitOptions}
            value={selectedAssignTarget}
            onChange={(_event, value) => {
              setAssignMemberState((current) => current ? { ...current, targetUnitId: value?.unitId ?? null } : current);
            }}
            getOptionLabel={(option) => option.label}
            isOptionEqualToValue={(option, value) => option.unitId === value.unitId}
            renderInput={(params) => (
              <TextField {...params} label="Объединение" placeholder="Выберите объединение" />
            )}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeAssignMemberDialog}>Отмена</Button>
          <Button variant="contained" disabled={isAssigningMember || !assignMemberState?.targetUnitId} onClick={() => void submitAssignMember()}>
            {isAssigningMember ? 'Определяем...' : 'Определить'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(deleteDialogState)} onClose={closeDeleteDialog} maxWidth="lg" fullWidth>
        <DialogTitle>Удаление объединения</DialogTitle>
        <DialogContent dividers>
          {deleteDialogState ? (
            <Stack spacing={1.4}>
              <Alert severity={deleteDialogState.willReassign ? 'warning' : 'info'} variant="outlined">
                {deleteDialogState.willReassign
                  ? 'Удаление перенесет прямых сотрудников в родительское объединение и поднимет дочерние узлы на уровень выше.'
                  : 'Группа будет удалена без переноса сотрудников.'}
              </Alert>

              <Typography sx={{ fontSize: 15, fontWeight: 700 }}>{deleteDialogState.unit.name}</Typography>

              <Box>
                <Typography sx={{ mb: 1, fontSize: 14, fontWeight: 700 }}>Предпросмотр новой иерархии</Typography>
                <UnitOrgChart
                  tree={deleteDialogState.previewTree}
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
