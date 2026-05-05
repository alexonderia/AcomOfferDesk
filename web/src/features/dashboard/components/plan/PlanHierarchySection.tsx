import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import CheckRoundedIcon from "@mui/icons-material/CheckRounded";
import ChevronRightRoundedIcon from "@mui/icons-material/ChevronRightRounded";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import Diversity3OutlinedIcon from "@mui/icons-material/Diversity3Outlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import LanOutlinedIcon from "@mui/icons-material/LanOutlined";
import ManageSearchRoundedIcon from "@mui/icons-material/ManageSearchRounded";
import MoreHorizRoundedIcon from "@mui/icons-material/MoreHorizRounded";
import PeopleAltOutlinedIcon from "@mui/icons-material/PeopleAltOutlined";
import PersonAddAlt1RoundedIcon from "@mui/icons-material/PersonAddAlt1Rounded";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import TrendingUpRoundedIcon from "@mui/icons-material/TrendingUpRounded";
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  IconButton,
  InputAdornment,
  LinearProgress,
  Menu,
  MenuItem,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { PlanTreeNode } from "@shared/api/plans";
import { formatAmount } from "@shared/lib/formatters";
import { planSectionCardSx } from "./PlanOverviewSections";
import type { PlanSideSummaryData } from "./planDashboardUtils";
import { formatPercent, getInitials } from "./planDashboardUtils";

export type PlanHierarchyHandlers = {
  onCreateSubplan: (node: PlanTreeNode) => void;
  onDelegate: (node: PlanTreeNode) => void;
  onEdit: (node: PlanTreeNode) => void;
  onDelete: (node: PlanTreeNode) => void;
  onClosePlan: (node: PlanTreeNode) => void;
};

type PlanNodeMetricGridProps = {
  node: PlanTreeNode;
};

export const PlanNodeMetricChips = ({ node }: PlanNodeMetricGridProps) => {
  const theme = useTheme();
  const metricItems = [
    { label: "План узла", value: formatAmount(node.plan_amount) },
    { label: "Личный план", value: formatAmount(node.personal_plan_amount) },
    { label: "Распределено", value: formatAmount(node.delegated_amount) },
    {
      label: "Выполнено по плану",
      value: formatAmount(node.fact_amount_subtree),
    },
    {
      label: "Выполнено за период",
      value: formatAmount(node.period_fact_amount ?? 0),
    },
    { label: "Выполнено лично", value: formatAmount(node.fact_amount_self) },
    { label: "Не распределено", value: formatAmount(node.unallocated_amount) },
    { label: "Выполнение", value: formatPercent(node.progress_percent) },
  ];

  return (
    <Box
      sx={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: { xs: 0.65, lg: 1.65 },
        minHeight: 28,
        borderTop: `1px solid ${alpha(theme.palette.divider, 0.86)}`,
        borderRadius: "0 0 10px 10px",
        px: { xs: 1, md: 2.25 },
        py: 0.42,
        bgcolor: alpha(theme.palette.background.default, 0.18),
      }}
    >
      {metricItems.map((metric) => (
        <Box
          key={metric.label}
          sx={{
            display: "inline-flex",
            alignItems: "baseline",
            gap: 0.35,
            px: 0,
            py: 0,
            bgcolor: "transparent",
            minWidth: 0,
          }}
        >
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontSize: 10.3, lineHeight: 1.1, whiteSpace: "nowrap" }}
          >
            {metric.label}
          </Typography>
          <Typography
            variant="caption"
            fontWeight={800}
            sx={{ fontSize: 10.8, lineHeight: 1.1, whiteSpace: "nowrap" }}
          >
            {metric.value}
          </Typography>
        </Box>
      ))}
    </Box>
  );
};

type PlanTreeNodeCardProps = {
  node: PlanTreeNode;
  depth: number;
  expandedNodeIds: Record<number, boolean>;
  forceExpanded: boolean;
  onToggle: (planId: number) => void;
  handlers: PlanHierarchyHandlers;
};

export const PlanTreeNodeCard = ({
  node,
  depth,
  expandedNodeIds,
  forceExpanded,
  onToggle,
  handlers,
}: PlanTreeNodeCardProps) => {
  const theme = useTheme();
  const isCompactActions = useMediaQuery(theme.breakpoints.down("md"));
  const [actionsAnchorEl, setActionsAnchorEl] = useState<null | HTMLElement>(
    null,
  );
  const hasChildren = node.children.length > 0;
  const isExpanded = forceExpanded || expandedNodeIds[node.plan_id] !== false;
  const progressValue = Math.max(0, Math.min(100, node.progress_percent));
  const periodProgressValue = Math.max(0, Math.min(100, node.period_progress_percent ?? 0));
  const isRoot = depth === 0;
  const isSyntheticRoot =
    isRoot && node.children.some((child) => child.user_id === node.user_id);
  const planTitle = node.plan_name?.trim() || node.user_name;
  const showExecutorName =
    !isSyntheticRoot &&
    node.user_name.trim().length > 0 &&
    node.user_name !== planTitle;

  const iconButtonSx = {
    width: 30,
    height: 30,
    borderRadius: `${theme.acomShape.controlRadius}px`,
    border: `1px solid ${alpha(theme.palette.primary.main, 0.45)}`,
    color: theme.palette.primary.main,
    bgcolor: theme.palette.background.paper,
    p: 0,
    "&:hover": {
      bgcolor: alpha(theme.palette.primary.main, 0.06),
      borderColor: alpha(theme.palette.primary.main, 0.7),
    },
  } as const;

  const actions = [
    node.available_actions.create_subplan
      ? {
          key: "create-subplan",
          title: "Создать подплан",
          icon: <LanOutlinedIcon sx={{ fontSize: 18 }} />,
          onClick: () => handlers.onCreateSubplan(node),
        }
      : null,
    node.available_actions.delegate_plan
      ? {
          key: "delegate",
          title: "Делегировать",
          icon: <Diversity3OutlinedIcon sx={{ fontSize: 18 }} />,
          onClick: () => handlers.onDelegate(node),
        }
      : null,
    node.available_actions.edit_plan
      ? {
          key: "edit",
          title: "Редактировать",
          icon: <EditOutlinedIcon sx={{ fontSize: 18 }} />,
          onClick: () => handlers.onEdit(node),
        }
      : null,
    node.available_actions.close_plan
      ? {
          key: "close",
          title: "Закрыть план",
          icon: <CheckRoundedIcon sx={{ fontSize: 18 }} />,
          onClick: () => handlers.onClosePlan(node),
        }
      : null,
    node.available_actions.delete_child_plan
      ? {
          key: "delete",
          title: "Удалить",
          icon: <DeleteOutlineOutlinedIcon sx={{ fontSize: 18 }} />,
          onClick: () => handlers.onDelete(node),
        }
      : null,
  ].filter((item): item is NonNullable<typeof item> => item !== null);

  const visibleInlineActions =
    isCompactActions && actions.length > 2 ? actions.slice(0, 1) : actions;
  const hiddenActions =
    isCompactActions && actions.length > 2 ? actions.slice(1) : [];

  return (
    <Box
      sx={{
        position: "relative",
        pl: depth === 0 ? 0 : { xs: 2, md: 2.8 },
        backgroundColor: "transparent",
      }}
    >
      <Stack
        direction="row"
        spacing={0.65}
        alignItems="flex-start"
        sx={{ position: "relative", zIndex: 1 }}
      >
        <IconButton
          size="small"
          onClick={() => (hasChildren ? onToggle(node.plan_id) : undefined)}
          sx={{
            mt: 0.1,
            width: 36,
            height: 36,
            borderRadius: `${theme.acomShape.controlRadius}px`,
            border: `1px solid ${alpha(theme.palette.primary.main, 0.34)}`,
            color: theme.palette.primary.main,
            bgcolor: theme.palette.background.paper,
            transform:
              hasChildren && isExpanded ? "rotate(90deg)" : "rotate(0deg)",
            transition: "transform 0.2s ease",
            boxShadow: `0 6px 14px ${alpha(theme.palette.primary.main, 0.06)}`,
            "&:hover": {
              bgcolor: hasChildren
                ? alpha(theme.palette.primary.main, 0.05)
                : theme.palette.background.paper,
              borderColor: alpha(
                theme.palette.primary.main,
                hasChildren ? 0.58 : 0.34,
              ),
            },
          }}
        >
          <ChevronRightRoundedIcon sx={{ fontSize: 20 }} />
        </IconButton>
        <Card
          sx={{
            ...planSectionCardSx,
            width: "100%",
            position: "relative",
            zIndex: 1,
            backgroundColor: theme.palette.background.paper,
            border: `1px solid ${alpha(theme.palette.divider, 0.86)}`,
            boxShadow: `0 8px 18px ${alpha(theme.palette.common.black, 0.018)}`,
            borderRadius: `${theme.acomShape.controlRadius}px`,
            overflow: "hidden",
          }}
        >
          <CardContent sx={{ p: 0, "&:last-child": { pb: 0 } }}>
            <Stack spacing={0} sx={{ position: "relative", zIndex: 3 }}>
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: {
                    xs: "1fr",
                    md: "minmax(240px, 0.88fr) minmax(210px, 1.25fr) minmax(128px, auto) auto",
                  },
                  gap: { xs: 0.65, md: 0.9 },
                  alignItems: "center",
                  minHeight: 52,
                  px: { xs: 1.05, md: 1.2 },
                  py: { xs: 0.75, md: 0.7 },
                }}
              >
                <Stack
                  direction="row"
                  spacing={0.9}
                  minWidth={0}
                  alignItems="center"
                >
                  {isSyntheticRoot ? (
                    <Box
                        sx={{
                          width: 38,
                          height: 38,
                          borderRadius: `${theme.acomShape.buttonRadius}px`,
                        bgcolor: alpha(theme.palette.primary.main, 0.12),
                        color: "primary.main",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      <AccountTreeOutlinedIcon sx={{ fontSize: 18 }} />
                    </Box>
                  ) : (
                    <Avatar
                      sx={{
                        width: 38,
                        height: 38,
                        bgcolor:
                          depth % 3 === 1
                            ? alpha(theme.palette.primary.main, 0.13)
                            : depth % 3 === 2
                              ? alpha(theme.palette.success.main, 0.15)
                              : alpha(theme.palette.warning.main, 0.16),
                        color:
                          depth % 3 === 1
                            ? theme.palette.primary.main
                            : depth % 3 === 2
                              ? theme.palette.success.dark
                              : theme.palette.warning.dark,
                        fontWeight: 800,
                        fontSize: 13.5,
                      }}
                    >
                      {getInitials(node.user_name)}
                    </Avatar>
                  )}
                  <Stack spacing={0.45} minWidth={0}>
                    <Stack
                      direction="row"
                      spacing={0.6}
                      alignItems="center"
                      flexWrap="wrap"
                      useFlexGap
                    >
                      <Typography
                        variant="body2"
                        fontWeight={800}
                        sx={{
                          overflowWrap: "anywhere",
                          lineHeight: 1.1,
                          fontSize: 14.2,
                        }}
                      >
                        {planTitle}
                      </Typography>
                      <Chip
                        size="small"
                        label={
                          isSyntheticRoot ? "Корневой узел" : node.user_role
                        }
                        sx={{
                          bgcolor: isSyntheticRoot
                            ? alpha(theme.palette.primary.main, 0.1)
                            : alpha(theme.palette.text.secondary, 0.08),
                          color: isSyntheticRoot
                            ? "primary.main"
                            : "text.secondary",
                          height: 17,
                          border: "none",
                          "& .MuiChip-label": {
                            px: 0.65,
                            fontWeight: isSyntheticRoot ? 700 : 600,
                            fontSize: 10.5,
                          },
                        }}
                      />
                    </Stack>
                    {showExecutorName ? (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ fontSize: 11.3, lineHeight: 1.1 }}
                      >
                        {node.user_name}
                      </Typography>
                    ) : null}
                  </Stack>
                </Stack>
                <Stack direction="row" spacing={0.75} alignItems="center" minWidth={0}>
                  <Box sx={{ flex: 1, position: "relative" }}>
                    <LinearProgress
                      variant="determinate"
                      value={progressValue}
                      sx={{
                        height: 7,
                        borderRadius: 999,
                        bgcolor: alpha(theme.palette.divider, 0.58),
                        "& .MuiLinearProgress-bar": {
                          borderRadius: 999,
                          backgroundColor:
                            progressValue >= 100
                              ? theme.palette.success.main
                              : theme.palette.primary.main,
                        },
                      }}
                    />
                    <LinearProgress
                      variant="determinate"
                      value={periodProgressValue}
                      sx={{
                        position: "absolute",
                        inset: 0,
                        height: 7,
                        borderRadius: 999,
                        bgcolor: "transparent",
                        "& .MuiLinearProgress-bar": {
                          borderRadius: 999,
                          backgroundColor: theme.palette.warning.main,
                        },
                      }}
                    />
                  </Box>
                  <Typography
                    variant="caption"
                    fontWeight={800}
                    sx={{ minWidth: 50, textAlign: "right", fontSize: 12 }}
                  >
                    {formatPercent(node.progress_percent)}
                  </Typography>
                </Stack>
                <Typography
                  variant="body2"
                  fontWeight={800}
                  sx={{
                    whiteSpace: "nowrap",
                    fontSize: 13,
                    textAlign: { xs: "left", md: "right" },
                  }}
                >
                  {formatAmount(node.fact_amount_subtree)} /
                  {formatAmount(node.plan_amount)}
                </Typography>
                <Stack
                  direction="row"
                  spacing={0.4}
                  alignItems="center"
                  justifyContent={{ xs: "flex-start", md: "flex-end" }}
                >
                  {actions.length > 0 ? (
                    <Stack
                      direction="row"
                      spacing={0.35}
                      justifyContent="flex-end"
                      flexWrap="nowrap"
                    >
                      {visibleInlineActions.map((action) => (
                        <Tooltip key={action.key} title={action.title}>
                          <IconButton
                            size="small"
                            onClick={action.onClick}
                            sx={iconButtonSx}
                          >
                            {action.icon}
                          </IconButton>
                        </Tooltip>
                      ))}
                      {hiddenActions.length > 0 ? (
                        <>
                          <IconButton
                            size="small"
                            onClick={(event) =>
                              setActionsAnchorEl(event.currentTarget)
                            }
                            sx={iconButtonSx}
                          >
                            <MoreHorizRoundedIcon sx={{ fontSize: 18 }} />
                          </IconButton>
                          <Menu
                            anchorEl={actionsAnchorEl}
                            open={Boolean(actionsAnchorEl)}
                            onClose={() => setActionsAnchorEl(null)}
                            anchorOrigin={{
                              vertical: "bottom",
                              horizontal: "right",
                            }}
                            transformOrigin={{
                              vertical: "top",
                              horizontal: "right",
                            }}
                          >
                            {hiddenActions.map((action) => (
                              <MenuItem
                                key={action.key}
                                onClick={() => {
                                  setActionsAnchorEl(null);
                                  action.onClick();
                                }}
                              >
                                {action.title}
                              </MenuItem>
                            ))}
                          </Menu>
                        </>
                      ) : null}
                    </Stack>
                  ) : null}
                </Stack>
              </Box>
              <PlanNodeMetricChips node={node} />
            </Stack>
          </CardContent>
        </Card>
      </Stack>

      {hasChildren && isExpanded ? (
        <Stack
          spacing={0}
          sx={{
            pt: 0,
            backgroundColor: "transparent",
            position: "relative",
            zIndex: 0,
          }}
        >
          {node.children.map((child) => (
            <PlanTreeNodeCard
              key={child.plan_id}
              node={child}
              depth={depth + 1}
              expandedNodeIds={expandedNodeIds}
              forceExpanded={forceExpanded}
              onToggle={onToggle}
              handlers={handlers}
            />
          ))}
        </Stack>
      ) : null}
    </Box>
  );
};

type PlanSideSummaryProps = {
  data: PlanSideSummaryData;
  unplannedSubordinates?: Array<{ id: string; name: string; role: string }>;
};

export const PlanSideSummary = ({
  data,
  unplannedSubordinates = [],
}: PlanSideSummaryProps) => {
  const navigate = useNavigate();
  const theme = useTheme();

  return (
    <Stack spacing={1}>
      <Card sx={planSectionCardSx}>
        <CardContent sx={{ p: 1.15, "&:last-child": { pb: 1.15 } }}>
          <Stack spacing={1.1}>
            <Stack
              direction="row"
              justifyContent="space-between"
              spacing={1}
              alignItems="center"
            >
              <Stack direction="row" spacing={0.9} alignItems="center">
                <PeopleAltOutlinedIcon
                  sx={{ color: "primary.main", fontSize: 20 }}
                />
                <Typography variant="subtitle1" fontWeight={800}>
                  Подчиненные без плана
                </Typography>
              </Stack>
              {unplannedSubordinates.length > 0 ? (
                <Chip
                  size="small"
                  label={String(unplannedSubordinates.length)}
                  sx={{ bgcolor: alpha(theme.palette.primary.main, 0.16) }}
                />
              ) : null}
            </Stack>
            {unplannedSubordinates.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                Нет подчиненных без плана.
              </Typography>
            ) : (
              <Stack spacing={1}>
                {unplannedSubordinates.slice(0, 3).map((employee) => (
                  <Stack
                    key={employee.id}
                    direction="row"
                    spacing={0.9}
                    alignItems="center"
                  >
                    <Avatar
                      sx={{
                        width: 38,
                        height: 38,
                        bgcolor: alpha(theme.palette.warning.main, 0.22),
                        color: theme.palette.warning.dark,
                        fontSize: 13,
                        fontWeight: 800,
                      }}
                    >
                      {getInitials(employee.name)}
                    </Avatar>
                    <Box minWidth={0}>
                      <Typography
                        variant="body2"
                        fontWeight={700}
                        sx={{ overflowWrap: "anywhere" }}
                      >
                        {employee.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {employee.role}
                      </Typography>
                    </Box>
                  </Stack>
                ))}
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<PersonAddAlt1RoundedIcon />}
                >
                  Назначить план
                </Button>
              </Stack>
            )}
          </Stack>
        </CardContent>
      </Card>
      <Card sx={planSectionCardSx}>
        <CardContent sx={{ p: 1.15, "&:last-child": { pb: 1.15 } }}>
          <Stack spacing={1.1}>
            <Stack direction="row" spacing={0.9} alignItems="center">
              <TrendingUpRoundedIcon
                sx={{ color: "primary.main", fontSize: 20 }}
              />
              <Typography variant="subtitle1" fontWeight={800}>
                Загрузка (личная)
              </Typography>
            </Stack>
            <Stack spacing={1.15}>
              <Box>
                <Typography variant="body2" fontWeight={700}>
                  Ваша личная загрузка
                </Typography>
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  spacing={1}
                  sx={{ mt: 0.45, mb: 0.35 }}
                >
                  <Typography variant="caption" color="text.secondary">
                    {data.personalFactAmount !== null &&
                    data.personalFactAmount !== undefined
                      ? `${formatAmount(data.personalFactAmount)} / ${formatAmount(data.personalPlanAmount ?? 0)}`
                      : "—"}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {data.personalProgressPercent !== null &&
                    data.personalProgressPercent !== undefined
                      ? formatPercent(data.personalProgressPercent)
                      : "—"}
                  </Typography>
                </Stack>
                <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.55 }}>
                  Заявок в работе: {data.personalInProgressRequestsCount ?? 0}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={Math.max(
                    0,
                    Math.min(100, data.personalProgressPercent ?? 0),
                  )}
                  sx={{
                    height: 7,
                    borderRadius: 999,
                    bgcolor: alpha(theme.palette.primary.main, 0.2),
                  }}
                />
              </Box>
              <Divider />
              <Box>
                <Typography variant="body2" fontWeight={700}>
                  Загрузка прямых подчиненных
                </Typography>
                {!data.directSubordinates || data.directSubordinates.length === 0 ? (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: "block", mt: 0.45 }}
                  >
                    Прямых подчиненных нет
                  </Typography>
                ) : (
                  <Stack spacing={0.85} sx={{ mt: 0.6 }}>
                    {data.directSubordinates.map((employee) => (
                      <Box key={employee.userId}>
                        <Typography
                          variant="caption"
                          fontWeight={700}
                          sx={{ display: "block", lineHeight: 1.1 }}
                        >
                          {employee.userName}
                        </Typography>
                        <Stack
                          direction="row"
                          justifyContent="space-between"
                          spacing={1}
                          sx={{ mb: 0.25 }}
                        >
                          <Typography variant="caption" color="text.secondary">
                            {`${formatAmount(employee.factAmount)} / ${formatAmount(employee.planAmount)}`}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatPercent(employee.progressPercent)}
                          </Typography>
                        </Stack>
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{ display: "block", mb: 0.4 }}
                        >
                          Заявок в работе: {employee.inProgressRequestsCount}
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={Math.max(0, Math.min(100, employee.progressPercent))}
                          color="success"
                          sx={{
                            height: 6,
                            borderRadius: 999,
                            bgcolor: alpha(theme.palette.success.main, 0.2),
                          }}
                        />
                      </Box>
                    ))}
                  </Stack>
                )}
              </Box>
            </Stack>
            <Button
              variant="text"
              endIcon={<ChevronRightRoundedIcon />}
              onClick={() => navigate("/pm-dashboard")}
              sx={{ justifyContent: "flex-start", px: 0 }}
            >
              Перейти к сотрудникам
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
};

type PlanHierarchySectionProps = {
  trees: PlanTreeNode[];
  searchValue: string;
  expandedNodeIds: Record<number, boolean>;
  forceExpanded: boolean;
  handlers: PlanHierarchyHandlers;
  sideSummary: PlanSideSummaryData;
  onSearchChange: (value: string) => void;
  onToggleNode: (planId: number) => void;
  onExpandAll: () => void;
  onCollapseAll: () => void;
};

export const PlanHierarchySection = ({
  trees,
  searchValue,
  expandedNodeIds,
  forceExpanded,
  handlers,
  sideSummary,
  onSearchChange,
  onToggleNode,
  onExpandAll,
  onCollapseAll,
}: PlanHierarchySectionProps) => {
  const hasItems = trees.length > 0;
  const theme = useTheme();

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: { xs: "1fr", xl: "minmax(0, 1fr) 292px" },
        gap: 1,
        alignItems: "start",
      }}
    >
      <Card
        sx={{
          ...planSectionCardSx,
          overflow: "visible",
          boxShadow: `0 10px 28px ${alpha(theme.palette.common.black, 0.025)}`,
          border: `1px solid ${alpha(theme.palette.divider, 0.72)}`,
          backgroundColor: theme.palette.background.paper,
          borderRadius: `${theme.acomShape.controlRadius}px`,
        }}
      >
        <CardContent
          sx={{
            p: { xs: 0.9, md: 1 },
            "&:last-child": { pb: { xs: 0.9, md: 1 } },
          }}
        >
          <Stack spacing={0.9}>
            <Stack
              direction={{ xs: "column", lg: "row" }}
              justifyContent="space-between"
              spacing={1}
              alignItems={{ xs: "stretch", lg: "center" }}
              sx={{
                minHeight: 31,
                px: { xs: 0.15, md: 0.3 },
              }}
            >
              <Typography
                variant="subtitle1"
                fontWeight={800}
                sx={{ fontSize: 24, lineHeight: 1.1 }}
              >
                Иерархия плана
              </Typography>
              <Stack
                direction={{ xs: "column", md: "row" }}
                spacing={0.75}
                alignItems={{ xs: "stretch", md: "center" }}
              >
                <Button
                  variant="outlined"
                  size="small"
                  onClick={onExpandAll}
                  startIcon={<ManageSearchRoundedIcon />}
                  sx={{
                    minHeight: 36,
                    height: 36,
                    whiteSpace: "nowrap",
                    px: 1.55,
                    borderRadius: `${theme.acomShape.controlRadius}px`,
                    borderColor: alpha(theme.palette.primary.main, 0.18),
                    color: theme.palette.primary.main,
                    bgcolor: theme.palette.background.paper,
                    fontSize: 13,
                    fontWeight: 700,
                    "&:hover": {
                      borderColor: alpha(theme.palette.primary.main, 0.4),
                      backgroundColor: alpha(theme.palette.primary.main, 0.06),
                    },
                  }}
                >
                  Развернуть все
                </Button>
                <Button
                  variant="text"
                  size="small"
                  onClick={onCollapseAll}
                  sx={{ display: "none" }}
                >
                  Свернуть все
                </Button>
                <TextField
                  size="small"
                  placeholder="Поиск по узлам"
                  value={searchValue}
                  onChange={(event) => onSearchChange(event.target.value)}
                  sx={{
                    minWidth: { xs: "100%", md: 205 },
                    "& .MuiOutlinedInput-root": {
                      minHeight: 36,
                      height: 36,
                      borderRadius: `${theme.acomShape.controlRadius}px`,
                      backgroundColor: theme.palette.background.paper,
                      fontSize: 13,
                    },
                    "& .MuiInputBase-input": {
                      py: 0.72,
                      fontSize: 13,
                    },
                  }}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <SearchRoundedIcon fontSize="small" />
                      </InputAdornment>
                    ),
                  }}
                />
              </Stack>
            </Stack>
            <Divider
              sx={{ borderColor: alpha(theme.palette.divider, 0.7), mx: -1 }}
            />
            <Stack spacing={0.6}>
              {!hasItems ? (
                <Card
                  variant="outlined"
                  sx={{ borderRadius: `${theme.acomShape.controlRadius}px`, borderColor: theme.palette.divider }}
                >
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      По текущему фильтру не найдено ни одного узла плана.
                    </Typography>
                  </CardContent>
                </Card>
              ) : (
                trees.map((node) => (
                  <PlanTreeNodeCard
                    key={node.plan_id}
                    node={node}
                    depth={0}
                    expandedNodeIds={expandedNodeIds}
                    forceExpanded={forceExpanded}
                    onToggle={onToggleNode}
                    handlers={handlers}
                  />
                ))
              )}
            </Stack>
          </Stack>
        </CardContent>
      </Card>
      <Box
        sx={{
          position: { xs: "static", xl: "sticky" },
          top: { xl: 12 },
          zIndex: 2,
        }}
      >
        <PlanSideSummary data={sideSummary} />
      </Box>
    </Box>
  );
};
