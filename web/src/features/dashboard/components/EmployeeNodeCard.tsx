import {
  Box,
  Chip,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { ResponsibilityEmployeeNode } from '@shared/api/users/getResponsibilityDashboard';
import { formatUnavailabilityDate, getUnavailabilityStatusLabel, type UnavailabilityPeriodInfo } from '@shared/lib/unavailability';
import {
  getUpcomingUrgency,
  getRelativeAvailabilityLabel,
  getNodeTotals,
  collectDescendantTotals,
  sumTotals,
  formatUnavailabilityRange,
  type ExpandedState,
} from './dashboardUtils';
import { ChevronUpIcon, ChevronDownIcon, SegmentedProgressBar } from './DashboardCharts';

const treeLineColor = alpha('#64748b', 0.28);

const EmployeeNodeCard = ({
  node,
  level,
  expanded,
  onToggle,
  statusColors,
  activeUnavailabilityByUser,
  upcomingUnavailabilityByUser,
}: {
  node: ResponsibilityEmployeeNode;
  level: number;
  expanded: ExpandedState;
  onToggle: (userId: string) => void;
  statusColors: Record<string, string>;
  activeUnavailabilityByUser: Record<string, UnavailabilityPeriodInfo>;
  upcomingUnavailabilityByUser: Record<string, UnavailabilityPeriodInfo>;
}) => {
  const ownTotals = getNodeTotals(node.statuses);
  const subordinatesTotals = collectDescendantTotals(node);
  const hasSubordinates = node.children.length > 0;
  const isExpanded = expanded[node.user_id] ?? true;
  const activeUnavailability = activeUnavailabilityByUser[node.user_id] ?? null;
  const upcomingUnavailability = upcomingUnavailabilityByUser[node.user_id] ?? null;
  const upcomingUrgency = upcomingUnavailability ? getUpcomingUrgency(upcomingUnavailability.startedAt) : null;
  const upcomingRelativeLabel = upcomingUnavailability ? getRelativeAvailabilityLabel(upcomingUnavailability.startedAt) : null;
  const ownCount = sumTotals(ownTotals);
  const subordinatesCount = sumTotals(subordinatesTotals);

  return (
    <Box sx={{ minWidth: 0, position: 'relative' }}>
      <Box
        sx={{
          borderRadius: 1.5,
          border: '1px solid',
          borderColor: level === 0 ? alpha('#2563eb', 0.22) : 'divider',
          backgroundColor: level === 0 ? alpha('#2563eb', 0.04) : 'background.paper',
          px: 1.25,
          py: 1,
        }}
      >
        <Stack spacing={0.85}>
          <Stack direction="row" spacing={1} alignItems="flex-start" justifyContent="space-between">
            <Box sx={{ minWidth: 0, flex: 1 }}>
              <Typography
                sx={{
                  fontWeight: 700,
                  fontSize: 14,
                  lineHeight: 1.25,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
                title={node.full_name || node.user_id}
              >
                {node.full_name || node.user_id}
              </Typography>
              <Stack direction="row" spacing={0.75} alignItems="center" flexWrap="wrap" useFlexGap sx={{ mt: 0.35 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                  {node.role_name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  · В работе: {ownCount}
                </Typography>
                {hasSubordinates ? (
                  <Typography variant="caption" color="text.secondary">
                    · Подчинённые: {subordinatesCount}
                  </Typography>
                ) : null}
              </Stack>
            </Box>
            {hasSubordinates ? (
              <Tooltip title={isExpanded ? 'Свернуть' : 'Развернуть'}>
                <IconButton
                  size="small"
                  onClick={() => onToggle(node.user_id)}
                  aria-label={isExpanded ? 'Свернуть подчинённых' : 'Развернуть подчинённых'}
                  aria-expanded={isExpanded}
                  sx={{ mt: -0.25, mr: -0.5, color: 'text.secondary' }}
                >
                  {isExpanded ? <ChevronUpIcon /> : <ChevronDownIcon />}
                </IconButton>
              </Tooltip>
            ) : null}
          </Stack>

          {(activeUnavailability || upcomingUnavailability) ? (
            <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
              {activeUnavailability ? (
                <Chip
                  size="small"
                  color="error"
                  variant="outlined"
                  label={`${getUnavailabilityStatusLabel(activeUnavailability.status)} до ${formatUnavailabilityDate(activeUnavailability.endedAt)}`}
                />
              ) : null}
              {upcomingUnavailability ? (
                <Chip
                  size="small"
                  color={upcomingUrgency === 'soon' ? 'warning' : 'default'}
                  variant="outlined"
                  label={`${getUnavailabilityStatusLabel(upcomingUnavailability.status)} с ${formatUnavailabilityDate(upcomingUnavailability.startedAt)}`}
                />
              ) : null}
            </Stack>
          ) : null}

          <Box>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.35 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                Личная загрузка
              </Typography>
              {ownCount > 0 ? (
                <Typography variant="caption" color="text.secondary">
                  {ownCount}
                </Typography>
              ) : null}
            </Stack>
            <SegmentedProgressBar totals={ownTotals} statusColors={statusColors} height={10} />
          </Box>

          {hasSubordinates ? (
            <Box>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.35 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                  Загрузка подчинённых
                </Typography>
                {subordinatesCount > 0 ? (
                  <Typography variant="caption" color="text.secondary">
                    {subordinatesCount}
                  </Typography>
                ) : null}
              </Stack>
              <SegmentedProgressBar totals={subordinatesTotals} statusColors={statusColors} height={10} />
            </Box>
          ) : null}

          {activeUnavailability ? (
            <Typography variant="caption" color="error.main">
              Сейчас недоступен: {getUnavailabilityStatusLabel(activeUnavailability.status)} ({formatUnavailabilityRange(activeUnavailability)})
            </Typography>
          ) : null}
          {upcomingUnavailability ? (
            <Typography variant="caption" color={upcomingUrgency === 'soon' ? 'warning.main' : 'text.secondary'}>
              Будет недоступен: {getUnavailabilityStatusLabel(upcomingUnavailability.status)} ({formatUnavailabilityRange(upcomingUnavailability)})
              {upcomingRelativeLabel ? `, ${upcomingRelativeLabel}` : ''}
            </Typography>
          ) : null}
        </Stack>
      </Box>

      {hasSubordinates && isExpanded ? (
        <Box
          sx={{
            mt: 0.55,
            ml: 1.75,
            pl: 1.5,
            borderLeft: `2px solid ${treeLineColor}`,
            display: 'flex',
            flexDirection: 'column',
            gap: 0.55,
          }}
        >
          {node.children.map((child) => (
            <Box key={child.user_id} sx={{ position: 'relative' }}>
              <Box
                sx={{
                  position: 'absolute',
                  left: -24,
                  top: 18,
                  width: 22,
                  height: 2,
                  bgcolor: treeLineColor,
                  borderRadius: 999,
                }}
              />
              <EmployeeNodeCard
                node={child}
                level={level + 1}
                expanded={expanded}
                onToggle={onToggle}
                statusColors={statusColors}
                activeUnavailabilityByUser={activeUnavailabilityByUser}
                upcomingUnavailabilityByUser={upcomingUnavailabilityByUser}
              />
            </Box>
          ))}
        </Box>
      ) : null}
    </Box>
  );
};

export { EmployeeNodeCard };
