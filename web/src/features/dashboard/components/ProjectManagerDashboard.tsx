import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  MenuItem,
  Select,
  Stack,
  Tab,
  Tabs,
  Tooltip,
  Typography,
  useTheme
} from '@mui/material';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  getResponsibilityDashboard,
  type ResponsibilityEmployeeNode,
  type ResponsibilityDashboardRequest,
  type ResponsibilityUpcomingUnavailability
} from '@shared/api/users/getResponsibilityDashboard';
import { useAuth } from '@app/providers/AuthProvider';
import { formatDate } from '@shared/lib/formatters';
import { useIsMobileViewport } from '@shared/lib/responsive';
import { updateRequestDetails } from '@shared/api/requests/updateRequestDetails';
import { ROLE } from '@shared/constants/roles';
import { ActionButton } from '@shared/components/ActionButton';
import { StatusPill, type StatusPillTone } from '@shared/components/StatusPill';
import { UnavailableAwareMenuItem } from '@shared/components/UnavailableAwareMenuItem';
import { formatUnavailabilityDate, type UnavailabilityPeriodInfo } from '@shared/lib/unavailability';
import {
  STATUS_LABELS,
  type AssignmentState,
  type ExpandedState,
  getDaysUntil,
  getActiveUnavailability,
  toPeriodInfo,
  formatUnavailabilitySummary,
  getRequestOwnerWarningTooltip,
  flattenEmployees,
  collectGlobalTotals,
  sumTotals,
} from './dashboardUtils';
import { CircularProcessChart, EmployeeWorkloadChart } from './DashboardCharts';
import { EmployeeNodeCard } from './EmployeeNodeCard';

const getRequestStatusTone = (status: string): StatusPillTone => {
  if (status === 'open') {
    return 'success';
  }
  if (status === 'review') {
    return 'warning';
  }
  return 'neutral';
};

export const ProjectManagerDashboard = () => {
  const { session } = useAuth();
  const theme = useTheme();
  const isMobileViewport = useIsMobileViewport();
  const statusColors = useMemo<Record<string, string>>(() => ({
    open: theme.palette.dashboard.status.open,
    review: theme.palette.dashboard.status.review
  }), [theme]);
  const workloadColors = useMemo(() => theme.palette.dashboard.workload, [theme]);
  const isLeadEconomist = session?.roleId === ROLE.LEAD_ECONOMIST;

  const [tree, setTree] = useState<ResponsibilityEmployeeNode[]>([]);
  const [unassignedRequests, setUnassignedRequests] = useState<ResponsibilityDashboardRequest[]>([]);
  const [myRequests, setMyRequests] = useState<ResponsibilityDashboardRequest[]>([]);
  const [assignedRequests, setAssignedRequests] = useState<ResponsibilityDashboardRequest[]>([]);
  const [activeUnavailability, setActiveUnavailability] = useState<ResponsibilityUpcomingUnavailability[]>([]);
  const [upcomingUnavailability, setUpcomingUnavailability] = useState<Array<{
    user_id: string;
    full_name: string | null;
    role_name: string;
    status: string;
    started_at: string;
    ended_at: string;
  }>>([]);
  const [requestsTab, setRequestsTab] = useState<'unassigned' | 'mine' | 'assigned'>('unassigned');
  const [assignmentState, setAssignmentState] = useState<AssignmentState>({});
  const [expandedNodes, setExpandedNodes] = useState<ExpandedState>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isAssigning, setIsAssigning] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [dismissedWarningKey, setDismissedWarningKey] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const response = await getResponsibilityDashboard();
      setTree(response.tree);
      setUnassignedRequests(response.unassignedRequests);
      setMyRequests(response.myRequests);
      setAssignedRequests(response.assignedRequests);
      setActiveUnavailability(response.activeUnavailability);
      setUpcomingUnavailability(response.upcomingUnavailability);
      setExpandedNodes((prev) => {
        const next = { ...prev };
        for (const node of flattenEmployees(response.tree)) {
          if (node.children.length > 0 && next[node.user_id] === undefined) {
            next[node.user_id] = false;
          }
        }
        return next;
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Не удалось загрузить дашборд');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    if (!isLeadEconomist && requestsTab === 'mine') {
      setRequestsTab('unassigned');
    }
  }, [isLeadEconomist, requestsTab]);

  const allSubordinates = useMemo(() => flattenEmployees(tree), [tree]);
  const globalTotals = useMemo(() => collectGlobalTotals(tree), [tree]);
  const inProgressTotal = useMemo(() => sumTotals(globalTotals), [globalTotals]);

  const pendingAssignmentIds = useMemo(
    () => Object.entries(assignmentState).filter(([, ownerId]) => Boolean(ownerId)).map(([requestId]) => Number(requestId)),
    [assignmentState]
  );

  const employeeNameById = useMemo(() => {
    return allSubordinates.reduce<Record<string, string>>((acc, employee) => {
      acc[employee.user_id] = employee.full_name || employee.user_id;
      return acc;
    }, {});
  }, [allSubordinates]);

  const resolveAssigneeLabel = useCallback((request: ResponsibilityDashboardRequest, userId: string) => {
    if (!userId) {
      return 'Выберите ответственного';
    }

    const employee = allSubordinates.find((item) => item.user_id === userId);
    if (employee) {
      return `${employee.full_name || employee.user_id} (${employee.role_name})`;
    }

    return request.owner_full_name || employeeNameById[userId] || userId;
  }, [allSubordinates, employeeNameById]);

  const activeUnavailabilityByUser = useMemo(
    () =>
      activeUnavailability.reduce<Record<string, UnavailabilityPeriodInfo>>((acc, period) => {
        acc[period.user_id] = toPeriodInfo(period);
        return acc;
      }, {}),
    [activeUnavailability]
  );

  const upcomingUnavailabilityByUser = useMemo(
    () =>
      upcomingUnavailability.reduce<Record<string, UnavailabilityPeriodInfo>>((acc, period) => {
        if (!acc[period.user_id]) {
          acc[period.user_id] = toPeriodInfo(period);
        }
        return acc;
      }, {}),
    [upcomingUnavailability]
  );

  const warningGroups = useMemo(
    () => ({
      active: activeUnavailability.map((period) => ({
        key: `active-${period.user_id}-${period.started_at}-${period.ended_at}`,
        text: formatUnavailabilitySummary(period.full_name || period.user_id, toPeriodInfo(period), '')
      })),
      upcoming: upcomingUnavailability.flatMap((period) => {
        const daysUntil = getDaysUntil(period.started_at);
        if (daysUntil !== 7 && (daysUntil === null || daysUntil > 3)) {
          return [];
        }

        return [{
          key: `upcoming-${period.user_id}-${period.started_at}-${period.ended_at}-${daysUntil}`,
          text: formatUnavailabilitySummary(period.full_name || period.user_id, toPeriodInfo(period), '')
        }];
      })
    }),
    [activeUnavailability, upcomingUnavailability]
  );

  const warningEntries = useMemo(
    () => [...warningGroups.active, ...warningGroups.upcoming],
    [warningGroups]
  );

  const warningKey = useMemo(
    () => warningEntries.map((entry) => entry.key).join('|'),
    [warningEntries]
  );

  const isWarningVisible = warningEntries.length > 0 && warningKey !== dismissedWarningKey;

  const visibleRequests = useMemo(() => {
    if (requestsTab === 'unassigned') {
      return unassignedRequests;
    }
    if (requestsTab === 'mine') {
      return myRequests;
    }
    return assignedRequests;
  }, [assignedRequests, myRequests, requestsTab, unassignedRequests]);

  const handleAssigneeChange = (requestId: number, ownerId: string) => {
    if (ownerId) {
      const active = getActiveUnavailability(ownerId, activeUnavailability);

      if (active) {
        const start = formatUnavailabilityDate(active.startedAt);
        const end = formatUnavailabilityDate(active.endedAt);
        setErrorMessage(`Нельзя назначить ответственного: сотрудник сейчас недоступен (${start} — ${end})`);
        return;
      }
    }

    setAssignmentState((prev) => ({ ...prev, [requestId]: ownerId }));
  };

  const toggleNode = (userId: string) => {
    setExpandedNodes((prev) => ({ ...prev, [userId]: !(prev[userId] ?? false) }));
  };

  const applyAssignments = async (requestIds: number[]) => {
    const prepared = requestIds
      .map((requestId) => ({ requestId, ownerUserId: assignmentState[requestId] }))
      .filter((item): item is { requestId: number; ownerUserId: string } => Boolean(item.ownerUserId));

    if (prepared.length === 0) {
      setErrorMessage('Выберите ответственного хотя бы для одной заявки');
      return;
    }

    setErrorMessage(null);
    setSuccessMessage(null);
    setIsAssigning(true);

    try {
      await Promise.all(
        prepared.map((item) =>
          updateRequestDetails({
            requestId: item.requestId,
            owner_user_id: item.ownerUserId
          })
        )
      );
      setSuccessMessage(
        prepared.length === 1
          ? `Заявка #${prepared[0].requestId} назначена сотруднику`
          : `Распределено заявок: ${prepared.length}`
      );
      await loadDashboard();
      setAssignmentState((prev) => {
        const next = { ...prev };
        for (const item of prepared) {
          delete next[item.requestId];
        }
        return next;
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Не удалось назначить ответственных');
    } finally {
      setIsAssigning(false);
    }
  };

  const handleAssignSingle = async (requestId: number) => {
    await applyAssignments([requestId]);
  };

  const handleAssignAllChanged = async () => {
    await applyAssignments(pendingAssignmentIds);
  };

  useEffect(() => {
    if (!warningKey || dismissedWarningKey === null) {
      return;
    }

    if (warningKey !== dismissedWarningKey) {
      setDismissedWarningKey(null);
    }
  }, [dismissedWarningKey, warningKey]);

  return (
    <Stack spacing={2.5}>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Chip label={`Сотрудников: ${allSubordinates.length}`} color="primary" variant="outlined" size="small" />
        <Chip label={`Заявок в работе: ${inProgressTotal}`} color="info" variant="outlined" size="small" />
        <Chip label={`Нераспределённых: ${unassignedRequests.length}`} color="warning" variant="outlined" size="small" />
      </Stack>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', xl: '1fr 1fr' },
          gap: 2
        }}
      >
        <CircularProcessChart totals={globalTotals} statusColors={statusColors} />
        <EmployeeWorkloadChart employees={allSubordinates} workloadColors={workloadColors} />
      </Box>

      {errorMessage ? (
        <Alert severity="error" onClose={() => setErrorMessage(null)}>
          {errorMessage}
        </Alert>
      ) : null}
      {successMessage ? (
        <Alert severity="success" onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      ) : null}
      {isWarningVisible ? (
        <Alert severity="warning" onClose={() => setDismissedWarningKey(warningKey)}>
          <Stack spacing={0.5}>
            <Typography variant="body2" fontWeight={600}>
              Внимание: кто-то из сотрудников сейчас недоступен или скоро будет недоступен.
            </Typography>
            {warningGroups.active.length > 0 ? (
              <Box>
                <Typography variant="body2" fontWeight={600}>
                  Сейчас недоступны:
                </Typography>
                {warningGroups.active.map((entry) => (
                  <Typography key={entry.key} variant="body2">
                    {entry.text}
                  </Typography>
                ))}
              </Box>
            ) : null}
            {warningGroups.upcoming.length > 0 ? (
              <Box>
                <Typography variant="body2" fontWeight={600}>
                  Будут недоступны:
                </Typography>
                {warningGroups.upcoming.map((entry) => (
                  <Typography key={entry.key} variant="body2">
                    {entry.text}
                  </Typography>
                ))}
              </Box>
            ) : null}
          </Stack>
        </Alert>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', lg: '1.4fr 1fr' },
          gap: 2
        }}
      >
        <Card sx={{ borderRadius: 2 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>
              Занятость штата
            </Typography>
            {isLoading ? (
              <Typography color="text.secondary">Загрузка...</Typography>
            ) : tree.length === 0 ? (
              <Typography color="text.secondary">Подчинённые сотрудники не найдены</Typography>
            ) : (
              <Stack spacing={1.2}>
                {tree.map((node) => (
                  <EmployeeNodeCard
                    key={node.user_id}
                    node={node}
                    level={0}
                    expanded={expandedNodes}
                    onToggle={toggleNode}
                    statusColors={statusColors}
                    activeUnavailabilityByUser={activeUnavailabilityByUser}
                    upcomingUnavailabilityByUser={upcomingUnavailabilityByUser}
                  />
                ))}
              </Stack>
            )}
          </CardContent>
        </Card>

        <Card sx={{ borderRadius: 2 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 0, fontWeight: 700 }}>
              Заявки
            </Typography>
            {isLeadEconomist ? (
              <Tabs
                value={requestsTab}
                onChange={(_, value: 'unassigned' | 'mine' | 'assigned') => setRequestsTab(value)}
                variant={isMobileViewport ? 'scrollable' : 'standard'}
                allowScrollButtonsMobile={isMobileViewport}
                scrollButtons={isMobileViewport ? 'auto' : false}
                sx={{ mb: 2 }}
              >
                <Tab value="unassigned" label={`Нераспределённые (${unassignedRequests.length})`} />
                <Tab value="mine" label={`Мои (${myRequests.length})`} />
                <Tab value="assigned" label={`Распределённые (${assignedRequests.length})`} />
              </Tabs>
            ) : (
              <Tabs
                value={requestsTab}
                onChange={(_, value: 'unassigned' | 'mine' | 'assigned') => setRequestsTab(value)}
                variant={isMobileViewport ? 'scrollable' : 'standard'}
                allowScrollButtonsMobile={isMobileViewport}
                scrollButtons={isMobileViewport ? 'auto' : false}
                sx={{ mb: 2 }}
              >
                <Tab value="unassigned" label={`Нераспределённые (${unassignedRequests.length})`} />
                <Tab value="assigned" label={`Распределённые (${assignedRequests.length})`} />
              </Tabs>
            )}
            <Stack spacing={1.5}>
              {visibleRequests.length === 0 ? (
                requestsTab === 'mine' ? (
                  <Typography color="text.secondary">
                    Нет моих заявок в работе
                  </Typography>
                ) : (
                  <Typography color="text.secondary">
                    {requestsTab === 'unassigned'
                      ? 'Все заявки уже распределены по ответственным'
                      : 'Нет распределённых заявок в работе'}
                  </Typography>
                )
              ) : (
                visibleRequests.map((request) => {
                  const selectedOwner = assignmentState[request.request_id] ?? (requestsTab === 'unassigned' ? '' : request.owner_user_id);
                  const requestOwnerActiveUnavailability = activeUnavailabilityByUser[request.owner_user_id] ?? null;
                  const requestOwnerUpcomingUnavailability = upcomingUnavailabilityByUser[request.owner_user_id] ?? null;
                  const requestOwnerWarningTooltip = getRequestOwnerWarningTooltip({
                    activePeriod: requestOwnerActiveUnavailability,
                    upcomingPeriod: requestOwnerUpcomingUnavailability,
                  });
                  return (
                    <Card key={`${requestsTab}-${request.request_id}`} variant="outlined" sx={{ borderRadius: 2 }}>
                      <CardContent>
                        <Stack
                          direction={{ xs: 'column', md: 'row' }}
                          spacing={1.5}
                          justifyContent="space-between"
                          alignItems={{ xs: 'stretch', md: 'flex-start' }}
                        >
                          <Stack spacing={0.9} sx={{ minWidth: 0 }}>
                            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                              <Typography fontWeight={700}>Заявка #{request.request_id}</Typography>
                              <StatusPill
                                label={STATUS_LABELS[request.status] ?? request.status_label}
                                tone={getRequestStatusTone(request.status)}
                              />
                            </Stack>
                            <Typography variant="body2" color="text.secondary">
                              {request.description || 'Описание не указано'}
                            </Typography>
                            <Box
                              sx={{
                                border: '1px solid',
                                borderColor: 'divider',
                                borderRadius: 1.5,
                                px: 1.1,
                                py: 0.8,
                                display: 'grid',
                                gap: 0.6,
                                maxWidth: { xs: '100%', md: 480 }
                              }}
                            >
                              <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="center">
                                <Typography variant="caption" color="text.secondary">
                                  Дедлайн
                                </Typography>
                                <Typography variant="body2" sx={{ textAlign: 'right', overflowWrap: 'anywhere' }}>
                                  {formatDate(request.deadline_at)}
                                </Typography>
                              </Stack>
                              <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="center">
                                <Typography variant="caption" color="text.secondary">
                                  Ответственный
                                </Typography>
                                <Stack direction="row" spacing={0.6} alignItems="center" sx={{ minWidth: 0 }}>
                                  <Typography variant="body2" sx={{ textAlign: 'right', overflowWrap: 'anywhere' }}>
                                    {request.owner_full_name || employeeNameById[request.owner_user_id] || request.owner_user_id || '-'}
                                  </Typography>
                                  {requestsTab !== 'unassigned' && requestOwnerWarningTooltip ? (
                                    <Tooltip title={requestOwnerWarningTooltip} arrow>
                                      <Box
                                        component="span"
                                        tabIndex={0}
                                        role="img"
                                        aria-label={requestOwnerWarningTooltip}
                                        sx={{
                                          width: 18,
                                          height: 18,
                                          borderRadius: '50%',
                                          backgroundColor: requestOwnerActiveUnavailability ? '#fef2f2' : '#fff7ed',
                                          border: `1px solid ${requestOwnerActiveUnavailability ? '#ef4444' : '#f59e0b'}`,
                                          color: requestOwnerActiveUnavailability ? '#dc2626' : '#d97706',
                                          display: 'inline-flex',
                                          alignItems: 'center',
                                          justifyContent: 'center',
                                          fontSize: 12,
                                          fontWeight: 800,
                                          lineHeight: 1,
                                          cursor: 'help',
                                          flexShrink: 0
                                        }}
                                      >
                                        !
                                      </Box>
                                    </Tooltip>
                                  ) : null}
                                </Stack>
                              </Stack>
                            </Box>
                          </Stack>

                          <Stack
                            spacing={1}
                            sx={{ width: { xs: '100%', md: 300 }, minHeight: { md: 92 }, justifyContent: 'space-between' }}
                          >
                            <Select
                              size="small"
                              displayEmpty
                              fullWidth
                              value={selectedOwner}
                              renderValue={(value) => resolveAssigneeLabel(request, String(value ?? ''))}
                              onChange={(event) => handleAssigneeChange(request.request_id, String(event.target.value))}
                            >
                              <MenuItem value="">Выберите ответственного</MenuItem>
                              {allSubordinates.map((employee) => (
                                <UnavailableAwareMenuItem
                                  key={`${request.request_id}-${employee.user_id}`}
                                  value={employee.user_id}
                                  label={`${employee.full_name || employee.user_id} (${employee.role_name})`}
                                  unavailablePeriod={getActiveUnavailability(employee.user_id, activeUnavailability)}
                                />
                              ))}
                            </Select>

                            <Stack direction="row" justifyContent="flex-end" sx={{ pt: { xs: 0, md: 0.5 } }}>
                              <ActionButton
                                kind="outlined"
                                showNavigationIcons={false}
                                sx={{
                                  minWidth: 44,
                                  height: 36,
                                  px: 1.4,
                                  fontWeight: 600,
                                  borderColor: 'divider',
                                  color: 'text.secondary'
                                }}
                                onClick={() => void handleAssignSingle(request.request_id)}
                                disabled={!assignmentState[request.request_id] || isAssigning}
                              >
                                ОК
                              </ActionButton>
                            </Stack>
                          </Stack>
                        </Stack>
                        </CardContent>
                    </Card>
                  );
                })
              )}
            </Stack>
            {visibleRequests.length > 0 ? (
              <Button
                variant="contained"
                fullWidth
                sx={{ mt: 2 }}
                onClick={() => void handleAssignAllChanged()}
                disabled={pendingAssignmentIds.length === 0 || isAssigning}
              >
                {requestsTab === 'unassigned' ? 'Распределить заявки' : 'Сохранить изменения'}
              </Button>
            ) : null}
          </CardContent>
        </Card>
      </Box>
    </Stack>
  );
};
