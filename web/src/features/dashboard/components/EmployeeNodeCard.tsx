import {
  Card,
  CardContent,
  Chip,
  IconButton,
  Stack,
  Tooltip,
  Typography
} from '@mui/material';
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

export const EmployeeNodeCard = ({
  node,
  level,
  expanded,
  onToggle,
  statusColors,
  activeUnavailabilityByUser,
  upcomingUnavailabilityByUser
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
  const isExpanded = expanded[node.user_id] ?? false;
  const activeUnavailability = activeUnavailabilityByUser[node.user_id] ?? null;
  const upcomingUnavailability = upcomingUnavailabilityByUser[node.user_id] ?? null;
  const upcomingUrgency = upcomingUnavailability ? getUpcomingUrgency(upcomingUnavailability.startedAt) : null;
  const upcomingRelativeLabel = upcomingUnavailability ? getRelativeAvailabilityLabel(upcomingUnavailability.startedAt) : null;

  return (
    <Card
      variant="outlined"
      sx={{
        ml: level * 2,
        borderRadius: 2,
        borderColor: 'divider',
        background: level === 0 ? 'rgba(47,111,214,0.06)' : 'background.paper'
      }}
    >
      <CardContent sx={{ pb: '16px !important' }}>
        <Stack spacing={1.2}>
          <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}>
            <Stack spacing={0.5}>
              <Typography fontWeight={700}>{node.full_name || node.user_id}</Typography>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
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
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                <Chip size="small" label={node.role_name} />
                <Typography variant="caption" color="text.secondary">
                  В работе: {sumTotals(ownTotals)}
                </Typography>
                {hasSubordinates ? (
                  <Typography variant="caption" color="text.secondary">
                    Подчинённые: {sumTotals(subordinatesTotals)}
                  </Typography>
                ) : null}
              </Stack>
            </Stack>
            {hasSubordinates ? (
              <Tooltip title={isExpanded ? 'Свернуть' : 'Развернуть'}>
                <IconButton
                  size="small"
                  onClick={() => onToggle(node.user_id)}
                  aria-label={isExpanded ? 'Свернуть подчинённых' : 'Развернуть подчинённых'}
                  aria-expanded={isExpanded}
                  sx={{
                    p: 0,
                    color: 'primary.main',
                    backgroundColor: 'transparent',
                    border: 'none',
                    '&:hover': { backgroundColor: 'transparent' }
                  }}
                >
                  {isExpanded ? <ChevronUpIcon /> : <ChevronDownIcon />}
                </IconButton>
              </Tooltip>
            ) : null}
          </Stack>

          <Stack spacing={1}>
            <Typography variant="body2" fontWeight={600}>
              Личная загрузка
            </Typography>
            <SegmentedProgressBar totals={ownTotals} statusColors={statusColors} />
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

          {hasSubordinates ? (
            <Stack spacing={1}>
              <Typography variant="body2" fontWeight={600}>
                Загрузка подчинённых (суммарно)
              </Typography>
              <SegmentedProgressBar totals={subordinatesTotals} statusColors={statusColors} />
            </Stack>
          ) : null}
        </Stack>
      </CardContent>

      {hasSubordinates && isExpanded ? (
        <Stack spacing={1.2} sx={{ pb: 2, pr: 2, pl: 2 }}>
          {node.children.map((child) => (
            <EmployeeNodeCard
              key={child.user_id}
              node={child}
              level={level + 1}
              expanded={expanded}
              onToggle={onToggle}
              statusColors={statusColors}
              activeUnavailabilityByUser={activeUnavailabilityByUser}
              upcomingUnavailabilityByUser={upcomingUnavailabilityByUser}
            />
          ))}
        </Stack>
      ) : null}
    </Card>
  );
};
