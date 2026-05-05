import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "@app/providers/AuthProvider";
import {
  getPlanRequestStats,
  type PlanDelegateCandidate,
  type PlanRequestStats,
  type PlanTreeNode,
} from "@shared/api/plans";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { usePlanDashboard } from "../model/usePlanDashboard";
import { PlanDialogs } from "./plan/PlanDialogs";
import { PlanHierarchySection } from "./plan/PlanHierarchySection";
import {
  PlanAnalyticsCards,
  PlanKpiRow,
  PlanPageHeader,
  planSectionCardSx,
} from "./plan/PlanOverviewSections";
import {
  delegateSchema,
  editSchema,
  parseAmount,
  rootPlanSchema,
  subplanSchema,
  type DelegateFormValues,
  type EditFormValues,
  type RootPlanFormValues,
  type SubplanFormValues,
} from "./plan/planDashboardForms";
import {
  buildDistributionItems,
  buildExecutionSlices,
  buildPlanFilterOptions,
  buildRequestFactMetrics,
  buildSideSummaryData,
  countUniqueParticipants,
  deriveSummaryFromTrees,
  filterPlanTree,
  findPlanNodeByPlanId,
  findSubtreeByUserId,
  formatPeriodLabel,
  getExpandableNodeIds,
  normalizePlanTreesForPresentation,
  periodToDate,
} from "./plan/planDashboardUtils";

const emptyCardSx = {
  ...planSectionCardSx,
  backgroundColor: "#ffffff",
};

const ALL_LEAD_MANAGERS_SCOPE = "__all_lead_managers__";

type PlanLeadOption = {
  userId: string;
  label: string;
};

const toDateInputValue = (value: Date) => {
  const year = value.getFullYear();
  const month = `${value.getMonth() + 1}`.padStart(2, "0");
  const day = `${value.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const getMonthStartFromPeriod = (period: string) => `${period}-01`;

const getMonthEndFromPeriod = (period: string) => {
  const [yearString, monthString] = period.split("-");
  const year = Number.parseInt(yearString ?? "", 10);
  const month = Number.parseInt(monthString ?? "", 10);
  if (!Number.isFinite(year) || !Number.isFinite(month)) {
    return toDateInputValue(new Date());
  }
  return toDateInputValue(new Date(year, month, 0));
};

const toRuDate = (value: string) => {
  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString("ru-RU");
};

const buildRangePeriodLabel = (dateFrom: string, dateTo: string) => {
  const yearFrom = dateFrom.slice(0, 4);
  const yearTo = dateTo.slice(0, 4);
  const monthFrom = dateFrom.slice(5, 7);
  const monthTo = dateTo.slice(5, 7);

  if (
    yearFrom === yearTo &&
    dateFrom === `${yearFrom}-01-01` &&
    dateTo === `${yearFrom}-12-31`
  ) {
    return yearFrom;
  }

  if (yearFrom === yearTo && monthFrom === monthTo) {
    return formatPeriodLabel(`${yearFrom}-${monthFrom}`);
  }

  return `${toRuDate(dateFrom)} — ${toRuDate(dateTo)}`;
};

const isSingleMonthRange = (dateFrom: string, dateTo: string) => {
  const yearFrom = Number.parseInt(dateFrom.slice(0, 4), 10);
  const monthFrom = Number.parseInt(dateFrom.slice(5, 7), 10);
  const dayFrom = dateFrom.slice(8, 10);
  const yearTo = Number.parseInt(dateTo.slice(0, 4), 10);
  const monthTo = Number.parseInt(dateTo.slice(5, 7), 10);
  const dayTo = dateTo.slice(8, 10);
  if (
    !Number.isFinite(yearFrom)
    || !Number.isFinite(monthFrom)
    || !Number.isFinite(yearTo)
    || !Number.isFinite(monthTo)
  ) {
    return false;
  }
  if (yearFrom !== yearTo || monthFrom !== monthTo || dayFrom !== "01") {
    return false;
  }
  const monthEnd = new Date(yearFrom, monthFrom, 0).getDate();
  return dayTo === String(monthEnd).padStart(2, "0");
};

const flattenPlanNodes = (nodes: PlanTreeNode[]): PlanTreeNode[] => {
  const result: PlanTreeNode[] = [];
  const walk = (node: PlanTreeNode) => {
    result.push(node);
    node.children.forEach(walk);
  };
  nodes.forEach(walk);
  return result;
};

const collectLeadOptions = (nodes: PlanTreeNode[]): PlanLeadOption[] => {
  const optionsByUserId = new Map<string, PlanLeadOption>();
  flattenPlanNodes(nodes).forEach((node) => {
    const roleLabel = node.user_role.toLowerCase();
    if (!roleLabel.includes("ведущ")) {
      return;
    }
    if (!optionsByUserId.has(node.user_id)) {
      optionsByUserId.set(node.user_id, {
        userId: node.user_id,
        label: `${node.user_name} (${node.user_role})`,
      });
    }
  });

  return Array.from(optionsByUserId.values()).sort((left, right) =>
    left.label.localeCompare(right.label, "ru"),
  );
};

const collectOwnerIdsFromSubtree = (node: PlanTreeNode): Set<string> => {
  const userIds = new Set<string>();
  const walk = (current: PlanTreeNode) => {
    userIds.add(current.user_id);
    current.children.forEach(walk);
  };
  walk(node);
  return userIds;
};

export const ProjectManagerPlanDashboard = () => {
  const theme = useTheme();
  const { session } = useAuth();
  const {
    period,
    setPeriod,
    setDateFrom: setDashboardDateFrom,
    setDateTo: setDashboardDateTo,
    trees,
    summary: dashboardSummary,
    requestStats: dashboardRequestStats,
    isLoading,
    isMutating,
    canCreateRootPlan,
    rootPlanExists,
    errorMessage,
    successMessage,
    setSuccessMessage,
    createRoot,
    createSubplanNodeWithStart,
    delegate,
    updatePlanNode,
    removeChildPlan,
    closePlanNode,
    loadDelegateCandidates,
  } = usePlanDashboard();

  const [isRootDialogOpen, setIsRootDialogOpen] = useState(false);
  const [subplanNode, setSubplanNode] = useState<PlanTreeNode | null>(null);
  const [delegateNode, setDelegateNode] = useState<PlanTreeNode | null>(null);
  const [delegateCandidates, setDelegateCandidates] = useState<
    PlanDelegateCandidate[]
  >([]);
  const [isCandidatesLoading, setIsCandidatesLoading] = useState(false);
  const [editNode, setEditNode] = useState<PlanTreeNode | null>(null);
  const [deleteNode, setDeleteNode] = useState<PlanTreeNode | null>(null);
  const [closeNode, setCloseNode] = useState<PlanTreeNode | null>(null);
  const [dateFrom, setDateFrom] = useState<string>(() => getMonthStartFromPeriod(period));
  const [dateTo, setDateTo] = useState<string>(() => getMonthEndFromPeriod(period));
  const [selectedLeadUserId, setSelectedLeadUserId] = useState<string>(
    ALL_LEAD_MANAGERS_SCOPE,
  );
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [searchValue, setSearchValue] = useState("");
  const [expandedNodeIds, setExpandedNodeIds] = useState<
    Record<number, boolean>
  >({});
  const [selectedPlanRequestStats, setSelectedPlanRequestStats] = useState<PlanRequestStats | null>(null);

  const rootPlanForm = useForm<RootPlanFormValues>({
    resolver: zodResolver(rootPlanSchema),
    defaultValues: {
      name: "",
      periodStart: periodToDate(period),
      periodEnd: getMonthEndFromPeriod(period),
      planAmount: "",
    },
  });
  const subplanForm = useForm<SubplanFormValues>({
    resolver: zodResolver(subplanSchema),
    defaultValues: {
      name: "",
      childUserId: "",
      periodStart: periodToDate(period),
      periodEnd: getMonthEndFromPeriod(period),
      amount: "",
    },
  });
  const delegateForm = useForm<DelegateFormValues>({
    resolver: zodResolver(delegateSchema),
    defaultValues: {
      childUserId: "",
      childPeriodStart: periodToDate(period),
      childPlanAmount: "",
    },
  });
  const editForm = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    defaultValues: { name: "", periodEnd: "", planAmount: "" },
  });

  useEffect(() => {
    rootPlanForm.setValue("periodStart", periodToDate(period));
    rootPlanForm.setValue("periodEnd", getMonthEndFromPeriod(period));
    if (!subplanNode) {
      subplanForm.setValue("periodStart", periodToDate(period));
      subplanForm.setValue("periodEnd", getMonthEndFromPeriod(period));
    }
    if (!delegateNode) {
      delegateForm.setValue("childPeriodStart", periodToDate(period));
    }
  }, [
    delegateForm,
    delegateNode,
    period,
    rootPlanForm,
    subplanForm,
    subplanNode,
  ]);

  useEffect(() => {
    const nextPeriod = dateFrom.slice(0, 7);
    if (/^\d{4}-\d{2}$/.test(nextPeriod) && nextPeriod !== period) {
      setPeriod(nextPeriod);
    }
  }, [dateFrom, period, setPeriod]);

  useEffect(() => {
    setDashboardDateFrom(dateFrom);
    setDashboardDateTo(dateTo);
  }, [dateFrom, dateTo, setDashboardDateFrom, setDashboardDateTo]);

  useEffect(() => {
    const nodeForCandidates = delegateNode ?? subplanNode;
    if (!nodeForCandidates) {
      return;
    }

    let isMounted = true;
    setIsCandidatesLoading(true);
    loadDelegateCandidates(nodeForCandidates.plan_id)
      .then((items) => {
        if (isMounted) {
          setDelegateCandidates(items);
        }
      })
      .catch(() => {
        if (isMounted) {
          setDelegateCandidates([]);
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsCandidatesLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [delegateNode, loadDelegateCandidates, subplanNode]);

  const leadOptions = useMemo(() => collectLeadOptions(trees), [trees]);
  const periodLabel = useMemo(
    () => buildRangePeriodLabel(dateFrom, dateTo),
    [dateFrom, dateTo],
  );

  const selectedLeadExists =
    selectedLeadUserId === ALL_LEAD_MANAGERS_SCOPE ||
    leadOptions.some((option) => option.userId === selectedLeadUserId);

  useEffect(() => {
    if (!selectedLeadExists) {
      setSelectedLeadUserId(ALL_LEAD_MANAGERS_SCOPE);
    }
  }, [selectedLeadExists]);

  const periodFilteredTrees = trees;

  const selectedLeadOwnerIds = useMemo(() => {
    if (selectedLeadUserId === ALL_LEAD_MANAGERS_SCOPE) {
      return null;
    }

    const leadNode = periodFilteredTrees
      .map((rootNode) => findSubtreeByUserId(rootNode, selectedLeadUserId))
      .find((node): node is PlanTreeNode => node !== null);

    return leadNode
      ? collectOwnerIdsFromSubtree(leadNode)
      : new Set<string>([selectedLeadUserId]);
  }, [periodFilteredTrees, selectedLeadUserId]);

  const scopedTrees = useMemo(() => {
    if (!selectedLeadOwnerIds) {
      return periodFilteredTrees;
    }

    return periodFilteredTrees
      .map((rootNode) => findSubtreeByUserId(rootNode, selectedLeadUserId))
      .filter((node): node is PlanTreeNode => node !== null);
  }, [periodFilteredTrees, selectedLeadOwnerIds, selectedLeadUserId]);

  const planOptions = useMemo(
    () => buildPlanFilterOptions(scopedTrees),
    [scopedTrees],
  );
  const selectedPlanExists =
    selectedPlanId === null ||
    planOptions.some((option) => option.planId === selectedPlanId);

  useEffect(() => {
    if (!selectedPlanExists) {
      setSelectedPlanId(null);
    }
  }, [selectedPlanExists]);

  const presentationTrees = useMemo(
    () => normalizePlanTreesForPresentation(scopedTrees),
    [scopedTrees],
  );
  const expandableNodeIds = useMemo(
    () => getExpandableNodeIds(presentationTrees),
    [presentationTrees],
  );
  const selectedPlanTree = useMemo(
    () =>
      selectedPlanId
        ? findPlanNodeByPlanId(presentationTrees, selectedPlanId)
        : null,
    [presentationTrees, selectedPlanId],
  );

  useEffect(() => {
    if (!selectedPlanTree) {
      setSelectedPlanRequestStats(null);
      return;
    }
    let isMounted = true;
    getPlanRequestStats({
      dateFrom,
      dateTo,
      planId: selectedPlanTree.plan_id,
    })
      .then((stats) => {
        if (isMounted) {
          setSelectedPlanRequestStats(stats);
        }
      })
      .catch(() => {
        if (isMounted) {
          setSelectedPlanRequestStats(null);
        }
      });
    return () => {
      isMounted = false;
    };
  }, [dateFrom, dateTo, selectedPlanTree]);

  useEffect(() => {
    setExpandedNodeIds((prev) => {
      const next = { ...prev };
      expandableNodeIds.forEach((planId) => {
        if (next[planId] === undefined) {
          next[planId] = true;
        }
      });
      return next;
    });
  }, [expandableNodeIds]);

  const visibleTrees = useMemo(() => {
    const sourceTrees = selectedPlanTree
      ? [selectedPlanTree]
      : presentationTrees;
    if (!searchValue.trim()) {
      return sourceTrees;
    }

    return sourceTrees
      .map((node) => filterPlanTree(node, searchValue))
      .filter((node): node is PlanTreeNode => node !== null);
  }, [presentationTrees, searchValue, selectedPlanTree]);

  const scopedSummary = useMemo(
    () => deriveSummaryFromTrees(scopedTrees),
    [scopedTrees],
  );
  const participantCount = useMemo(
    () => countUniqueParticipants(scopedTrees),
    [scopedTrees],
  );
  const distributionItems = useMemo(
    () => buildDistributionItems(scopedTrees),
    [scopedTrees],
  );
  const executionSlices = useMemo(
    () => buildExecutionSlices(scopedTrees),
    [scopedTrees],
  );
  const requestFactMetrics = useMemo(
    () => {
      if (selectedPlanTree) {
        return buildRequestFactMetrics(
          {
            total_plan_amount: selectedPlanTree.plan_amount,
            total_fact_amount: selectedPlanTree.fact_amount_subtree,
            total_period_fact_amount: selectedPlanTree.period_fact_amount ?? 0,
            total_remaining_amount: selectedPlanTree.remaining_amount,
            total_progress_percent: selectedPlanTree.progress_percent,
            total_period_progress_percent: selectedPlanTree.period_progress_percent ?? 0,
          },
          selectedPlanRequestStats,
          selectedPlanTree.period_fact_amount ?? null,
          selectedPlanTree.period_progress_percent ?? null,
        );
      }
      return buildRequestFactMetrics(
        scopedSummary,
        dashboardRequestStats,
        dashboardSummary?.total_period_fact_amount ?? null,
        dashboardSummary?.total_period_progress_percent ?? null,
      );
    },
    [
      dashboardSummary?.total_period_fact_amount,
      dashboardSummary?.total_period_progress_percent,
      dashboardRequestStats,
      scopedSummary,
      selectedPlanRequestStats,
      selectedPlanTree,
    ],
  );
  const sideSummary = useMemo(
    () => buildSideSummaryData(scopedTrees, session?.userId ?? null),
    [scopedTrees, session?.userId],
  );
  const showNoPeriodExecutionHint = useMemo(() => {
    if (!isSingleMonthRange(dateFrom, dateTo)) {
      return false;
    }
    if (!rootPlanExists || scopedSummary.total_plan_amount <= 0) {
      return false;
    }
    return (requestFactMetrics.periodFactAmount ?? 0) <= 0;
  }, [
    dateFrom,
    dateTo,
    requestFactMetrics.periodFactAmount,
    rootPlanExists,
    scopedSummary.total_plan_amount,
  ]);
  const forceExpanded = Boolean(searchValue.trim());

  const openEditDialog = (node: PlanTreeNode) => {
    setEditNode(node);
    editForm.reset({
      name: node.plan_name,
      periodEnd: node.period_end,
      planAmount: node.plan_amount.toFixed(2),
    });
  };

  const hierarchyHandlers = {
    onCreateSubplan: (planNode: PlanTreeNode) => {
      setSubplanNode(planNode);
      subplanForm.reset({
        name: "",
        childUserId: planNode.user_id,
        periodStart: planNode.period_start,
        periodEnd: planNode.period_end,
        amount: "",
      });
    },
    onDelegate: (planNode: PlanTreeNode) => {
      setDelegateNode(planNode);
      delegateForm.reset({
        childUserId: "",
        childPeriodStart: planNode.period_start,
        childPlanAmount: "",
      });
    },
    onEdit: openEditDialog,
    onDelete: (planNode: PlanTreeNode) => setDeleteNode(planNode),
    onClosePlan: (planNode: PlanTreeNode) => setCloseNode(planNode),
  };

  const applyPlanSelection = (planId: number | null) => {
    setSelectedPlanId(planId);
    if (planId === null) {
      setExpandedNodeIds((prev) => {
        const next = { ...prev };
        expandableNodeIds.forEach((id) => {
          next[id] = true;
        });
        return next;
      });
      return;
    }

    const subtree = findPlanNodeByPlanId(presentationTrees, planId);
    if (!subtree) {
      return;
    }
    const subtreeExpandable = getExpandableNodeIds([subtree]);
    setExpandedNodeIds(
      subtreeExpandable.reduce<Record<number, boolean>>((acc, id) => {
        acc[id] = true;
        return acc;
      }, {}),
    );
  };

  const togglePlanSelection = (planId: number) => {
    applyPlanSelection(selectedPlanId === planId ? null : planId);
  };

  return (
    <Stack
      spacing={1.35}
      sx={{
        backgroundColor: "transparent",
        borderRadius: `${theme.acomShape.panelRadius}px`,
        p: { xs: 0.5, md: 0.75 },
      }}
    >
      
      <PlanPageHeader
        dateFrom={dateFrom}
        dateTo={dateTo}
        selectedLeadUserId={selectedLeadUserId}
        leadOptions={leadOptions}
        allLeadsValue={ALL_LEAD_MANAGERS_SCOPE}
        canCreateRootPlan={canCreateRootPlan}
        isMutating={isMutating}
        onDateFromChange={setDateFrom}
        onDateToChange={setDateTo}
        onLeadChange={setSelectedLeadUserId}
        onAddPlan={() => setIsRootDialogOpen(true)}
      />
      {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}
      {successMessage ? (
        <Alert severity="success" onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      ) : null}
      <PlanKpiRow
        totalPlanAmount={scopedSummary.total_plan_amount}
        totalFactAmount={scopedSummary.total_fact_amount}
        totalProgressPercent={scopedSummary.total_progress_percent}
        totalRemainingAmount={scopedSummary.total_remaining_amount}
        participantCount={participantCount}
      />
      {isLoading ? (
        <Card sx={emptyCardSx}>
          
          <CardContent sx={{ p: { xs: 1.35, md: 1.6 } }}>
            
            <Stack spacing={1}>
              
              <Skeleton variant="rounded" width="100%" height={96} />
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: {
                    xs: "1fr",
                    md: "repeat(2, minmax(0, 1fr))",
                    xl: "repeat(3, minmax(0, 1fr))",
                  },
                  gap: 1,
                }}
              >
                
                <Skeleton variant="rounded" width="100%" height={228} />
                <Skeleton variant="rounded" width="100%" height={228} />
                <Skeleton variant="rounded" width="100%" height={228} />
              </Box>
              <Skeleton variant="rounded" width="100%" height={320} />
            </Stack>
          </CardContent>
        </Card>
      ) : null}
      {!isLoading && !rootPlanExists ? (
        <Card sx={emptyCardSx}>
          
          <CardContent sx={{ py: 5.5 }}>
            
            <Stack spacing={1.25} alignItems="center" textAlign="center">
              
              <Box
                sx={{
                  width: 82,
                  height: 82,
                  borderRadius: `${theme.acomShape.surfaceRadius}px`,
                  bgcolor: alpha("#3b82f6", 0.08),
                  color: "primary.main",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 32,
                  fontWeight: 800,
                }}
              >
                
                ₽
              </Box>
              <Typography variant="h5" fontWeight={800}>
                
                План на выбранный период еще не создан
              </Typography>
              <Typography
                variant="body1"
                color="text.secondary"
                sx={{ maxWidth: 560 }}
              >
                
                Создайте общий план и распределите его между подчиненными, чтобы
                страница заполнилась метриками и иерархией.
              </Typography>
              {canCreateRootPlan ? (
                <Button
                  variant="contained"
                  onClick={() => setIsRootDialogOpen(true)}
                  disabled={isMutating}
                  sx={{ minWidth: 180 }}
                >
                  
                  Добавить план
                </Button>
              ) : null}
            </Stack>
          </CardContent>
        </Card>
      ) : null}
      {!isLoading && rootPlanExists ? (
        <>
          
          <PlanAnalyticsCards
            totalPlanAmount={scopedSummary.total_plan_amount}
            totalFactAmount={scopedSummary.total_fact_amount}
            totalProgressPercent={scopedSummary.total_progress_percent}
            totalRemainingAmount={scopedSummary.total_remaining_amount}
            periodLabel={periodLabel}
            distributionItems={distributionItems}
            executionSlices={executionSlices}
            selectedPlanId={selectedPlanId}
            requestFactMetrics={requestFactMetrics}
            showNoPeriodExecutionHint={showNoPeriodExecutionHint}
            selectedPlanLabel={
              selectedPlanTree
                ? `${selectedPlanTree.plan_name} (${selectedPlanTree.user_name})`
                : null
            }
            onExecutionSliceClick={togglePlanSelection}
            onDistributionItemClick={togglePlanSelection}
            onClearPlanSelection={() => applyPlanSelection(null)}
          />
          <PlanHierarchySection
            trees={visibleTrees}
            searchValue={searchValue}
            expandedNodeIds={expandedNodeIds}
            forceExpanded={forceExpanded}
            handlers={hierarchyHandlers}
            sideSummary={sideSummary}
            onSearchChange={setSearchValue}
            onToggleNode={(planId) =>
              setExpandedNodeIds((prev) => ({
                ...prev,
                [planId]: !prev[planId],
              }))
            }
            onExpandAll={() =>
              setExpandedNodeIds(
                expandableNodeIds.reduce<Record<number, boolean>>(
                  (acc, planId) => {
                    acc[planId] = true;
                    return acc;
                  },
                  {},
                ),
              )
            }
            onCollapseAll={() =>
              setExpandedNodeIds(
                expandableNodeIds.reduce<Record<number, boolean>>(
                  (acc, planId) => {
                    acc[planId] = false;
                    return acc;
                  },
                  {},
                ),
              )
            }
          />
        </>
      ) : null}
      <PlanDialogs
        isMutating={isMutating}
        canCreateRootPlan={canCreateRootPlan}
        rootDialogOpen={isRootDialogOpen}
        subplanNode={subplanNode}
        delegateNode={delegateNode}
        delegateCandidates={delegateCandidates}
        isCandidatesLoading={isCandidatesLoading}
        editNode={editNode}
        deleteNode={deleteNode}
        closeNode={closeNode}
        rootPlanForm={rootPlanForm}
        subplanForm={subplanForm}
        delegateForm={delegateForm}
        editForm={editForm}
        onCloseRootDialog={() => setIsRootDialogOpen(false)}
        onCloseSubplanDialog={() => setSubplanNode(null)}
        onCloseDelegateDialog={() => setDelegateNode(null)}
        onCloseEditDialog={() => setEditNode(null)}
        onCloseDeleteDialog={() => setDeleteNode(null)}
        onCloseCloseDialog={() => setCloseNode(null)}
        onSubmitRoot={rootPlanForm.handleSubmit(async (values) => {
          await createRoot(
            values.name,
            parseAmount(values.planAmount),
            values.periodStart,
            values.periodEnd,
          );
          rootPlanForm.reset({
            name: "",
            periodStart: periodToDate(period),
            periodEnd: getMonthEndFromPeriod(period),
            planAmount: "",
          });
          setIsRootDialogOpen(false);
        })}
        onSubmitSubplan={subplanForm.handleSubmit(async (values) => {
          if (!subplanNode) {
            return;
          }
          await createSubplanNodeWithStart(
            subplanNode.plan_id,
            values.name,
            parseAmount(values.amount),
            values.periodStart,
            values.periodEnd,
            values.childUserId,
          );
          setSubplanNode(null);
        })}
        onSubmitDelegate={delegateForm.handleSubmit(async (values) => {
          if (!delegateNode) {
            return;
          }
          await delegate(
            delegateNode.plan_id,
            values.childUserId,
            parseAmount(values.childPlanAmount),
            values.childPeriodStart,
          );
          setDelegateNode(null);
        })}
        onSubmitEdit={editForm.handleSubmit(async (values) => {
          if (!editNode) {
            return;
          }
          await updatePlanNode(editNode.plan_id, {
            name: values.name,
            periodEnd: values.periodEnd,
            planAmount: parseAmount(values.planAmount),
          });
          setEditNode(null);
        })}
        onConfirmDelete={async () => {
          if (!deleteNode) {
            return;
          }
          await removeChildPlan(deleteNode.plan_id);
          setDeleteNode(null);
        }}
        onConfirmClose={async () => {
          if (!closeNode) {
            return;
          }
          await closePlanNode(closeNode.plan_id);
          setCloseNode(null);
        }}
      />
    </Stack>
  );
};
