import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Collapse,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import ExpandLessRoundedIcon from '@mui/icons-material/ExpandLessRounded';
import ExpandMoreRoundedIcon from '@mui/icons-material/ExpandMoreRounded';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ReportPeriodSelector } from './shared/ReportPeriodSelector';
import {
  getResponsibilityDashboard,
  type ResponsibilityEmployeeNode,
  type ResponsibilityClosedSavingsItem,
  type ResponsibilitySavingsItem,
  type ResponsibilitySavingsSummary,
} from '@shared/api/users/getResponsibilityDashboard';
import { ROLE } from '@shared/constants/roles';
import { formatDate, formatAmount, formatSignedAmount } from '@shared/lib/formatters';
import { useIsMobileViewport } from '@shared/lib/responsive';

const emptySavings: ResponsibilitySavingsSummary = {
  total_closed_requests: 0,
  total_with_savings: 0,
  total_savings_amount: 0,
  closed_items: [],
  items: [],
};

const toDateInputValue = (value: Date) => {
  const year = value.getFullYear();
  const month = `${value.getMonth() + 1}`.padStart(2, '0');
  const day = `${value.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const getCurrentMonthStart = () => {
  const now = new Date();
  return toDateInputValue(new Date(now.getFullYear(), now.getMonth(), 1));
};

const getCurrentDate = () => toDateInputValue(new Date());


type ScopeFilterOption = {
  userId: string;
  label: string;
};

type LeadEconomistOption = ScopeFilterOption;
type ProjectFilterOption = { projectId: number; label: string };
const ALL_LEAD_ECONOMISTS_SCOPE = '__all_lead_economists__';
const ALL_PROJECTS_SCOPE = '__all_projects__';

const flattenEmployeeTree = (nodes: ResponsibilityEmployeeNode[]): ResponsibilityEmployeeNode[] => {
  const result: ResponsibilityEmployeeNode[] = [];
  const walk = (node: ResponsibilityEmployeeNode) => {
    result.push(node);
    node.children.forEach(walk);
  };
  nodes.forEach(walk);
  return result;
};

const collectLeadEconomistOptions = (nodes: ResponsibilityEmployeeNode[]): LeadEconomistOption[] =>
  flattenEmployeeTree(nodes)
    .filter((node) => node.role_id === ROLE.LEAD_ECONOMIST)
    .map((node) => ({
      userId: node.user_id,
      label: `${node.full_name ?? node.user_id} (${node.role_name})`,
    }))
    .sort((left, right) => left.label.localeCompare(right.label, 'ru'));

const findEmployeeNodeById = (
  nodes: ResponsibilityEmployeeNode[],
  userId: string
): ResponsibilityEmployeeNode | null => {
  for (const node of nodes) {
    if (node.user_id === userId) {
      return node;
    }
    const fromChild = findEmployeeNodeById(node.children, userId);
    if (fromChild) {
      return fromChild;
    }
  }
  return null;
};

const collectSubtreeUserIds = (node: ResponsibilityEmployeeNode): Set<string> => {
  const userIds = new Set<string>();
  const walk = (current: ResponsibilityEmployeeNode) => {
    userIds.add(current.user_id);
    current.children.forEach(walk);
  };
  walk(node);
  return userIds;
};

const PeriodRangeField = ({
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
}: {
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
}) => {
  return (
    <ReportPeriodSelector
      dateFrom={dateFrom}
      dateTo={dateTo}
      onDateFromChange={onDateFromChange}
      onDateToChange={onDateToChange}
      minWidth={390}
    />
  );
};

type SummaryListItem = {
  key: string;
  title: string;
  subtitle: string;
  amount?: string;
  amountColor?: 'text.primary' | 'success.main' | 'error.main';
};

const toSummaryListItem = (item: ResponsibilitySavingsItem | ResponsibilityClosedSavingsItem): SummaryListItem => ({
  key: `request-${item.request_id}`,
  title: `Заявка #${item.request_id}`,
  subtitle: `${item.owner_full_name || item.owner_user_id}${item.closed_at ? ` В· ${formatDate(item.closed_at)}` : ''}`,
  amount: typeof item.savings_amount === 'number' ? formatSignedAmount(item.savings_amount) : undefined,
  amountColor:
    typeof item.savings_amount === 'number'
      ? item.savings_amount >= 0
        ? 'success.main'
        : 'error.main'
      : undefined,
});

const toClosedSummaryListItem = (item: ResponsibilityClosedSavingsItem): SummaryListItem => {
  const base = toSummaryListItem(item);

  if (base.amount) {
    return base;
  }

  if (item.offer_amount === null) {
    return {
      ...base,
      amount: formatAmount(0),
      amountColor: 'text.primary',
    };
  }

  return base;
};

const SummaryListCard = ({
  title,
  value,
  valueColor = 'text.primary',
  items,
  emptyText,
  isExpanded,
  onToggle,
}: {
  title: string;
  value: string;
  valueColor?: 'text.primary' | 'success.main' | 'error.main';
  items: SummaryListItem[];
  emptyText: string;
  isExpanded: boolean;
  onToggle: () => void;
}) => {
  return (
    <Card variant="outlined" sx={{ borderRadius: 2, height: '100%' }}>
      <CardContent sx={{ height: '100%' }}>
        <Stack spacing={1.5} sx={{ height: '100%' }}>
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                {title}
              </Typography>
              <Typography variant="h5" fontWeight={800} color={valueColor}>
                {value}
              </Typography>
            </Box>
            <IconButton size="small" onClick={onToggle} aria-label={isExpanded ? 'Свернуть список' : 'Развернуть список'}>
              {isExpanded ? <ExpandLessRoundedIcon fontSize="small" /> : <ExpandMoreRoundedIcon fontSize="small" />}
            </IconButton>
          </Stack>

          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <Stack spacing={0.75} sx={{ maxHeight: 260, overflowY: 'auto', pr: 0.5 }}>
              {items.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  {emptyText}
                </Typography>
              ) : (
                items.map((item) => (
                  <Box
                    key={item.key}
                    sx={{
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1.5,
                      px: 1.25,
                      py: 1,
                      backgroundColor: 'background.paper',
                    }}
                  >
                    <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="flex-start">
                      <Stack spacing={0.2} sx={{ minWidth: 0 }}>
                        <Typography variant="body2" fontWeight={700}>
                          {item.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {item.subtitle}
                        </Typography>
                      </Stack>
                      {item.amount ? (
                        <Typography variant="body2" fontWeight={700} color={item.amountColor ?? 'text.primary'}>
                          {item.amount}
                        </Typography>
                      ) : null}
                    </Stack>
                  </Box>
                ))
              )}
            </Stack>
          </Collapse>
        </Stack>
      </CardContent>
    </Card>
  );
};

const roundPercent = (value: number) => Math.round(value * 10) / 10;
const toRadians = (angle: number) => (Math.PI / 180) * angle;

const describeSectorPath = (centerX: number, centerY: number, radius: number, startAngle: number, endAngle: number) => {
  const safeSweep = Math.min(Math.max(endAngle - startAngle, 0), 359.999);
  const startX = centerX + radius * Math.cos(toRadians(startAngle));
  const startY = centerY + radius * Math.sin(toRadians(startAngle));
  const endX = centerX + radius * Math.cos(toRadians(startAngle + safeSweep));
  const endY = centerY + radius * Math.sin(toRadians(startAngle + safeSweep));
  const largeArcFlag = safeSweep > 180 ? 1 : 0;

  return `M ${centerX} ${centerY} L ${startX} ${startY} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endX} ${endY} Z`;
};

const SavingsRatioChart = ({
  savingsAmount,
  lostSavingsAmount,
}: {
  savingsAmount: number;
  lostSavingsAmount: number;
}) => {
  const positiveSavings = Math.max(savingsAmount, 0);
  const totalLostSavings = Math.max(lostSavingsAmount, 0);
  const chartTotal = positiveSavings + totalLostSavings;
  const [activeSliceKey, setActiveSliceKey] = useState<'savings' | 'lost' | null>(null);

  if (chartTotal === 0) {
    return (
      <Card variant="outlined" sx={{ borderRadius: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 0.75 }}>
            Соотношение экономии
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Пока нет закрытых заявок с рассчитанной экономией.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const segments = [
    {
      key: 'savings' as const,
      label: 'Экономия',
      amount: positiveSavings,
      percent: (positiveSavings / chartTotal) * 100,
      color: '#2e7d32',
    },
    {
      key: 'lost' as const,
      label: 'Упущенная экономия',
      amount: totalLostSavings,
      percent: (totalLostSavings / chartTotal) * 100,
      color: '#d32f2f',
    },
  ].filter((segment) => segment.amount > 0.0001);

  const pieRadius = 80;
  let currentAngle = -90;
  const pieSegments = segments.map((segment) => {
    const sweep = (segment.amount / chartTotal) * 360;
    const endAngle = currentAngle + sweep;
    const result = {
      ...segment,
      startAngle: currentAngle,
      endAngle,
    };
    currentAngle = endAngle;
    return result;
  });

  return (
    <Card
      sx={{
        borderRadius: 2,
        background: 'linear-gradient(135deg, rgba(231,240,255,0.92), rgba(255,255,255,0.98))',
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <CardContent>
        <Typography variant="h6" sx={{ mb: 0.5, fontWeight: 700 }}>
          Соотношение экономии
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Диаграмма показывает долю найденной и упущенной экономии.
        </Typography>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '128px minmax(0, 1fr)', md: '220px minmax(0, 1fr)' },
            gap: { xs: 1.25, md: 2 },
            alignItems: 'center',
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Box
              sx={{
                position: 'relative',
                width: { xs: 128, md: 180 },
                height: { xs: 128, md: 180 },
                borderRadius: '50%',
                boxShadow: 'inset 0 0 0 1px rgba(47,111,214,0.16), 0 10px 24px rgba(31,42,68,0.12)',
              }}
            >
              <Box component="svg" viewBox="0 0 200 200" sx={{ width: '100%', height: '100%' }}>
                {pieSegments.map((segment) => (
                  <path
                    key={segment.key}
                    d={describeSectorPath(100, 100, pieRadius, segment.startAngle, segment.endAngle)}
                    fill={segment.color}
                    stroke="#ffffff"
                    strokeWidth={2}
                    style={{ cursor: 'pointer' }}
                    onMouseEnter={() => setActiveSliceKey(segment.key)}
                    onMouseLeave={() => setActiveSliceKey(null)}
                  >
                    <title>{`${segment.label}: ${formatAmount(segment.amount)}`}</title>
                  </path>
                ))}
              </Box>
            </Box>
          </Box>

          <Stack spacing={{ xs: 0.8, md: 1.25 }}>
            {pieSegments.map((segment) => (
              <Card
                key={segment.key}
                variant="outlined"
                sx={{
                  borderRadius: 2,
                  borderColor: activeSliceKey === segment.key ? segment.color : 'divider',
                }}
              >
                <CardContent sx={{ py: { xs: 0.75, md: 1.5 }, px: { xs: 1.1, md: 2 }, '&:last-child': { pb: { xs: 0.75, md: 1.5 } } }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={0.75}>
                    <Stack direction="row" spacing={0.75} alignItems="center" sx={{ minWidth: 0 }}>
                      <Box sx={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: segment.color, flexShrink: 0 }} />
                      <Typography variant="body2" fontWeight={600} noWrap>
                        {segment.label}
                      </Typography>
                    </Stack>
                    <Typography variant="body2" fontWeight={700} color={segment.key === 'savings' ? 'success.main' : 'error.main'} noWrap>
                      {formatAmount(segment.amount)} ({roundPercent(segment.percent)}%)
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            ))}

            <Card variant="outlined" sx={{ borderRadius: 2 }}>
              <CardContent sx={{ py: 1.25, '&:last-child': { pb: 1.25 } }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                  <Typography variant="body2" fontWeight={600}>
                    Всего экономии и упущенной
                  </Typography>
                  <Typography variant="body2" fontWeight={700} color="primary.main">
                    {formatAmount(chartTotal)}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Stack>
        </Box>
      </CardContent>
    </Card>
  );
};

const SavingsTzMetrics = ({
  leadOptions,
  selectedLeadUserId,
  onLeadUserChange,
  totalTzAmount,
  savingsAmount,
  lostSavingsAmount,
}: {
  leadOptions: LeadEconomistOption[];
  selectedLeadUserId: string;
  onLeadUserChange: (value: string) => void;
  totalTzAmount: number;
  savingsAmount: number;
  lostSavingsAmount: number;
}) => {
  const baseTzAmount = Math.max(totalTzAmount, 0);
  const positiveSavings = Math.max(savingsAmount, 0);
  const totalLostSavings = Math.max(lostSavingsAmount, 0);
  const savingsPercent = baseTzAmount > 0 ? (positiveSavings / baseTzAmount) * 100 : 0;
  const lostPercent = baseTzAmount > 0 ? (totalLostSavings / baseTzAmount) * 100 : 0;

  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 0.5, fontWeight: 700 }}>
          Показатели по ТЗ
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Проценты рассчитываются от общей суммы по ТЗ закрытых заявок.
        </Typography>
        <FormControl size="small" fullWidth sx={{ mb: 2 }}>
          <InputLabel id="tz-lead-economist-label">Выбор модуля по руководителю</InputLabel>
          <Select
            labelId="tz-lead-economist-label"
            label="Выбор модуля по руководителю"
            value={selectedLeadUserId}
            onChange={(event) => onLeadUserChange(event.target.value)}
            disabled={leadOptions.length === 0}
          >
            <MenuItem value={ALL_LEAD_ECONOMISTS_SCOPE}>Все руководители</MenuItem>
            {leadOptions.map((option) => (
              <MenuItem key={option.userId} value={option.userId}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Stack spacing={1.25}>
          <Card variant="outlined" sx={{ borderRadius: 2 }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <Typography variant="body2" fontWeight={600}>
                  Общая сумма по ТЗ
                </Typography>
                <Typography variant="body2" fontWeight={700} color="primary.main">
                  {formatAmount(baseTzAmount)}
                </Typography>
              </Stack>
            </CardContent>
          </Card>

          <Card variant="outlined" sx={{ borderRadius: 2 }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <Typography variant="body2" fontWeight={600}>
                  Найденная экономия от ТЗ
                </Typography>
                <Typography variant="body2" fontWeight={700} color="success.main">
                  {formatAmount(positiveSavings)} ({roundPercent(savingsPercent)}%)
                </Typography>
              </Stack>
            </CardContent>
          </Card>

          <Card variant="outlined" sx={{ borderRadius: 2 }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <Typography variant="body2" fontWeight={600}>
                  Упущенная экономия от ТЗ
                </Typography>
                <Typography variant="body2" fontWeight={700} color="error.main">
                  {formatAmount(totalLostSavings)} ({roundPercent(lostPercent)}%)
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      </CardContent>
    </Card>
  );
};

export const ProjectManagerSavingsDashboard = () => {
  const isMobileViewport = useIsMobileViewport();
  const [savings, setSavings] = useState<ResponsibilitySavingsSummary>(emptySavings);
  const [employeeTree, setEmployeeTree] = useState<ResponsibilityEmployeeNode[]>([]);
  const [dateFrom, setDateFrom] = useState<string>(getCurrentMonthStart);
  const [dateTo, setDateTo] = useState<string>(getCurrentDate);
  const [selectedGlobalLeadUserId, setSelectedGlobalLeadUserId] = useState<string>(ALL_LEAD_ECONOMISTS_SCOPE);
  const [selectedLeadUserId, setSelectedLeadUserId] = useState<string>(ALL_LEAD_ECONOMISTS_SCOPE);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(ALL_PROJECTS_SCOPE);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [expandedCards, setExpandedCards] = useState({
    closed: true,
    withSavings: true,
    savings: true,
    lost: true,
  });

  useEffect(() => {
    setExpandedCards({
      closed: !isMobileViewport,
      withSavings: !isMobileViewport,
      savings: !isMobileViewport,
      lost: !isMobileViewport
    });
  }, [isMobileViewport]);

  const loadSavings = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await getResponsibilityDashboard();
      setEmployeeTree(response.tree);
      setSavings(response.savings);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Не удалось загрузить статистику экономии');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSavings();
  }, [loadSavings]);

  const leadEconomistOptions = useMemo(
    () => collectLeadEconomistOptions(employeeTree),
    [employeeTree]
  );
  const selectedGlobalLeadExists =
    selectedGlobalLeadUserId === ALL_LEAD_ECONOMISTS_SCOPE ||
    leadEconomistOptions.some((option) => option.userId === selectedGlobalLeadUserId);
  const selectedLeadExists = leadEconomistOptions.some((option) => option.userId === selectedLeadUserId);

  useEffect(() => {
    if (!selectedGlobalLeadExists) {
      setSelectedGlobalLeadUserId(ALL_LEAD_ECONOMISTS_SCOPE);
    }
  }, [selectedGlobalLeadExists]);

  useEffect(() => {
    if (leadEconomistOptions.length === 0) {
      setSelectedLeadUserId(ALL_LEAD_ECONOMISTS_SCOPE);
      return;
    }
    if (!selectedLeadExists && selectedLeadUserId !== ALL_LEAD_ECONOMISTS_SCOPE) {
      setSelectedLeadUserId(ALL_LEAD_ECONOMISTS_SCOPE);
    }
  }, [leadEconomistOptions, selectedLeadExists, selectedLeadUserId]);

  const selectedGlobalLeadOwnerIds = useMemo(() => {
    if (selectedGlobalLeadUserId === ALL_LEAD_ECONOMISTS_SCOPE) {
      return null;
    }

    const node = findEmployeeNodeById(employeeTree, selectedGlobalLeadUserId);
    return node ? collectSubtreeUserIds(node) : new Set<string>([selectedGlobalLeadUserId]);
  }, [employeeTree, selectedGlobalLeadUserId]);

  const dateRange = useMemo(() => {
    const fromTime = Date.parse(`${dateFrom}T00:00:00`);
    const toTime = Date.parse(`${dateTo}T23:59:59.999`);

    if (!Number.isFinite(fromTime) || !Number.isFinite(toTime) || fromTime > toTime) {
      return null;
    }

    return {
      start: fromTime,
      end: toTime,
    };
  }, [dateFrom, dateTo]);

  const isInSelectedPeriod = useCallback(
    (closedAt: string | null) => {
      if (!dateRange || !closedAt) {
        return false;
      }

      const closedAtTime = new Date(closedAt).getTime();
      if (!Number.isFinite(closedAtTime)) {
        return false;
      }

      return closedAtTime >= dateRange.start && closedAtTime <= dateRange.end;
    },
    [dateRange]
  );

  const matchesGlobalFilters = useCallback(
    (ownerUserId: string, closedAt: string | null) => {
      if (!isInSelectedPeriod(closedAt)) {
        return false;
      }
      if (selectedGlobalLeadOwnerIds && !selectedGlobalLeadOwnerIds.has(ownerUserId)) {
        return false;
      }
      return true;
    },
    [isInSelectedPeriod, selectedGlobalLeadOwnerIds]
  );

  const filteredClosedItems = useMemo(
    () => (savings.closed_items ?? []).filter((item) => matchesGlobalFilters(item.owner_user_id, item.closed_at)),
    [matchesGlobalFilters, savings.closed_items]
  );

  const filteredSavingsItems = useMemo(
    () => savings.items.filter((item) => matchesGlobalFilters(item.owner_user_id, item.closed_at)),
    [matchesGlobalFilters, savings.items]
  );

  const projectOptions = useMemo<ProjectFilterOption[]>(() => {
    const byProjectId = new Map<number, string>();
    filteredClosedItems.forEach((item) => {
      if (item.plan_id == null) {
        return;
      }
      byProjectId.set(item.plan_id, item.plan_name?.trim() || `Проект #${item.plan_id}`);
    });
    return Array.from(byProjectId.entries())
      .map(([projectId, label]) => ({ projectId, label }))
      .sort((left, right) => left.label.localeCompare(right.label, 'ru'));
  }, [filteredClosedItems]);

  useEffect(() => {
    if (
      selectedProjectId !== ALL_PROJECTS_SCOPE
      && !projectOptions.some((item) => String(item.projectId) === selectedProjectId)
    ) {
      setSelectedProjectId(ALL_PROJECTS_SCOPE);
    }
  }, [projectOptions, selectedProjectId]);

  const projectFilteredClosedItems = useMemo(() => {
    if (selectedProjectId === ALL_PROJECTS_SCOPE) {
      return filteredClosedItems;
    }
    const projectId = Number.parseInt(selectedProjectId, 10);
    return filteredClosedItems.filter((item) => item.plan_id === projectId);
  }, [filteredClosedItems, selectedProjectId]);

  const projectFilteredSavingsItems = useMemo(() => {
    if (selectedProjectId === ALL_PROJECTS_SCOPE) {
      return filteredSavingsItems;
    }
    const projectId = Number.parseInt(selectedProjectId, 10);
    return filteredSavingsItems.filter((item) => item.plan_id === projectId);
  }, [filteredSavingsItems, selectedProjectId]);

  const periodFilteredClosedItems = useMemo(
    () => (savings.closed_items ?? []).filter((item) => isInSelectedPeriod(item.closed_at)),
    [isInSelectedPeriod, savings.closed_items]
  );

  const periodFilteredSavingsItems = useMemo(
    () => savings.items.filter((item) => isInSelectedPeriod(item.closed_at)),
    [isInSelectedPeriod, savings.items]
  );

  const projectFilteredPeriodClosedItems = useMemo(() => {
    if (selectedProjectId === ALL_PROJECTS_SCOPE) {
      return periodFilteredClosedItems;
    }
    const projectId = Number.parseInt(selectedProjectId, 10);
    return periodFilteredClosedItems.filter((item) => item.plan_id === projectId);
  }, [periodFilteredClosedItems, selectedProjectId]);

  const projectFilteredPeriodSavingsItems = useMemo(() => {
    if (selectedProjectId === ALL_PROJECTS_SCOPE) {
      return periodFilteredSavingsItems;
    }
    const projectId = Number.parseInt(selectedProjectId, 10);
    return periodFilteredSavingsItems.filter((item) => item.plan_id === projectId);
  }, [periodFilteredSavingsItems, selectedProjectId]);

  const selectedLeadOwnerIds = useMemo(() => {
    if (!selectedLeadUserId || selectedLeadUserId === ALL_LEAD_ECONOMISTS_SCOPE) {
      return null;
    }

    const leadNode = findEmployeeNodeById(employeeTree, selectedLeadUserId);
    return leadNode ? collectSubtreeUserIds(leadNode) : new Set<string>([selectedLeadUserId]);
  }, [employeeTree, selectedLeadUserId]);

  const tzClosedItems = useMemo(() => {
    if (!selectedLeadOwnerIds) {
      return projectFilteredPeriodClosedItems;
    }
    return projectFilteredPeriodClosedItems.filter((item) => selectedLeadOwnerIds.has(item.owner_user_id));
  }, [projectFilteredPeriodClosedItems, selectedLeadOwnerIds]);

  const tzSavingsItems = useMemo(() => {
    if (!selectedLeadOwnerIds) {
      return projectFilteredPeriodSavingsItems;
    }
    return projectFilteredPeriodSavingsItems.filter((item) => selectedLeadOwnerIds.has(item.owner_user_id));
  }, [projectFilteredPeriodSavingsItems, selectedLeadOwnerIds]);

  const itemsByClosed = useMemo(
    () =>
      [...projectFilteredClosedItems].sort((left, right) => {
        const leftTime = left.closed_at ? new Date(left.closed_at).getTime() : 0;
        const rightTime = right.closed_at ? new Date(right.closed_at).getTime() : 0;
        return rightTime - leftTime;
      }),
    [projectFilteredClosedItems]
  );

  const itemsWithSavings = useMemo(
    () => [...projectFilteredSavingsItems].sort((left, right) => Math.abs(right.savings_amount) - Math.abs(left.savings_amount)),
    [projectFilteredSavingsItems]
  );

  const positiveItems = useMemo(() => itemsWithSavings.filter((item) => item.savings_amount > 0), [itemsWithSavings]);

  const negativeItems = useMemo(() => itemsWithSavings.filter((item) => item.savings_amount < 0), [itemsWithSavings]);

  const summary = useMemo(() => {
    return projectFilteredSavingsItems.reduce(
      (acc, item) => {
        if (item.savings_amount > 0) {
          acc.totalSavings += item.savings_amount;
        } else {
          acc.lostSavings += Math.abs(item.savings_amount);
        }

        return acc;
      },
      { totalSavings: 0, lostSavings: 0 }
    );
  }, [projectFilteredSavingsItems]);

  const totalTzAmount = useMemo(
    () => {
      return tzClosedItems.reduce((acc, item) => {
        const amount = item.initial_amount ?? 0;
        return acc + (Number.isFinite(amount) ? amount : 0);
      }, 0);
    },
    [tzClosedItems]
  );

  const tzSummary = useMemo(() => {
    return tzSavingsItems.reduce(
      (acc, item) => {
        if (item.savings_amount > 0) {
          acc.totalSavings += item.savings_amount;
        } else {
          acc.lostSavings += Math.abs(item.savings_amount);
        }
        return acc;
      },
      { totalSavings: 0, lostSavings: 0 }
    );
  }, [tzSavingsItems]);

  const closedItemsList = useMemo(() => itemsByClosed.map((item) => toClosedSummaryListItem(item)), [itemsByClosed]);

  const withSavingsList = useMemo(() => itemsWithSavings.map((item) => toSummaryListItem(item)), [itemsWithSavings]);

  const positiveList = useMemo(() => positiveItems.map((item) => toSummaryListItem(item)), [positiveItems]);

  const negativeList = useMemo(() => negativeItems.map((item) => toSummaryListItem(item)), [negativeItems]);

  const toggleCard = (key: 'closed' | 'withSavings' | 'savings' | 'lost') => {
    setExpandedCards((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <Stack spacing={2.5}>
      <Stack
        direction={{ xs: 'column', xl: 'row' }}
        spacing={1.1}
        justifyContent="space-between"
        alignItems={{ xs: 'stretch', xl: 'center' }}
      >
        <Stack spacing={0.25} sx={{ minWidth: 0 }}>
          <Typography variant="h5" fontWeight={800} sx={{ lineHeight: 1.1, fontSize: { xs: 25, md: 26 } }}>
            Экономия
          </Typography>
        </Stack>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={1}
          alignItems={{ xs: 'stretch', sm: 'center' }}
          justifyContent={{ sm: 'flex-end' }}
          useFlexGap
          flexWrap="wrap"
        >
          <PeriodRangeField
            dateFrom={dateFrom}
            dateTo={dateTo}
            onDateFromChange={setDateFrom}
            onDateToChange={setDateTo}
          />
          <FormControl
            size="small"
            sx={{
              minWidth: { xs: '100%', sm: 256 },
              '& .MuiOutlinedInput-root': {
                minHeight: 40,
                bgcolor: 'rgba(255,255,255,0.96)',
              },
            }}
          >
            <InputLabel id="savings-scope-label">Выбор модуля по руководителю</InputLabel>
            <Select
              labelId="savings-scope-label"
              label="Выбор модуля по руководителю"
              value={selectedGlobalLeadUserId}
              onChange={(event) => setSelectedGlobalLeadUserId(event.target.value)}
            >
              <MenuItem value={ALL_LEAD_ECONOMISTS_SCOPE}>Все руководители</MenuItem>
              {leadEconomistOptions.map((option) => (
                <MenuItem key={option.userId} value={option.userId}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl
            size="small"
            sx={{
              minWidth: { xs: '100%', sm: 240 },
              '& .MuiOutlinedInput-root': {
                minHeight: 40,
                bgcolor: 'rgba(255,255,255,0.96)',
              },
            }}
          >
            <InputLabel id="savings-project-filter-label">Проект</InputLabel>
            <Select
              labelId="savings-project-filter-label"
              label="Проект"
              value={selectedProjectId}
              onChange={(event) => setSelectedProjectId(event.target.value)}
            >
              <MenuItem value={ALL_PROJECTS_SCOPE}>Все проекты</MenuItem>
              {projectOptions.map((option) => (
                <MenuItem key={option.projectId} value={String(option.projectId)}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </Stack>

      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Chip label={`Закрытых заявок: ${itemsByClosed.length}`} color="primary" variant="outlined" size="small" />
        <Chip label={`С расчетом экономии: ${itemsWithSavings.length}`} color="info" variant="outlined" size="small" />
        <Chip label={`С экономией: ${positiveItems.length}`} color="success" variant="outlined" size="small" />
        <Chip label={`С минусом: ${negativeItems.length}`} color="error" variant="outlined" size="small" />
      </Stack>

      {errorMessage ? (
        <Alert severity="error" onClose={() => setErrorMessage(null)}>
          {errorMessage}
        </Alert>
      ) : null}

      {isLoading ? (
        <Card sx={{ borderRadius: 2 }}>
          <CardContent>
            <Typography color="text.secondary">Загрузка...</Typography>
          </CardContent>
        </Card>
      ) : (
        <>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', xl: 'minmax(0, 1fr) minmax(0, 1fr)' },
              gap: 1.5,
            }}
          >
            <SavingsRatioChart savingsAmount={summary.totalSavings} lostSavingsAmount={summary.lostSavings} />
            <SavingsTzMetrics
              leadOptions={leadEconomistOptions}
              selectedLeadUserId={selectedLeadUserId}
              onLeadUserChange={setSelectedLeadUserId}
              totalTzAmount={totalTzAmount}
              savingsAmount={tzSummary.totalSavings}
              lostSavingsAmount={tzSummary.lostSavings}
            />
          </Box>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))', lg: 'repeat(4, minmax(0, 1fr))' },
              gap: 1.5,
            }}
          >
            <SummaryListCard
              title="Закрытые заявки"
              value={String(itemsByClosed.length)}
              items={closedItemsList}
              emptyText="Нет закрытых заявок с детализацией."
              isExpanded={expandedCards.closed}
              onToggle={() => toggleCard('closed')}
            />
            <SummaryListCard
              title="С расчетом экономии"
              value={String(itemsWithSavings.length)}
              items={withSavingsList}
              emptyText="Нет заявок с расчетом экономии."
              isExpanded={expandedCards.withSavings}
              onToggle={() => toggleCard('withSavings')}
            />
            <SummaryListCard
              title="Экономия"
              value={formatAmount(summary.totalSavings)}
              valueColor={summary.totalSavings > 0 ? 'success.main' : 'text.primary'}
              items={positiveList}
              emptyText="Нет заявок с экономией."
              isExpanded={expandedCards.savings}
              onToggle={() => toggleCard('savings')}
            />
            <SummaryListCard
              title="Упущенная экономия"
              value={formatAmount(summary.lostSavings)}
              valueColor="error.main"
              items={negativeList}
              emptyText="Нет заявок с отрицательной экономией."
              isExpanded={expandedCards.lost}
              onToggle={() => toggleCard('lost')}
            />
          </Box>
        </>
      )}
    </Stack>
  );
};

