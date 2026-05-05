import type {
  ResponsibilityEmployeeNode,
  ResponsibilityStatusCounter,
  ResponsibilityUpcomingUnavailability
} from '@shared/api/users/getResponsibilityDashboard';
import { formatUnavailabilityDate, getUnavailabilityStatusLabel, getUnavailabilityTooltip, type UnavailabilityPeriodInfo } from '@shared/lib/unavailability';

export const STATUS_LABELS: Record<string, string> = {
  open: 'Сбор КП',
  review: 'Анализ КП'
};

export type AssignmentState = Record<number, string>;
export type ExpandedState = Record<string, boolean>;
export type StatusTotals = Record<string, number>;

const MS_IN_DAY = 24 * 60 * 60 * 1000;

const startOfDay = (date: Date) => new Date(date.getFullYear(), date.getMonth(), date.getDate());

export const getDaysUntil = (value: string) => {
  const targetDate = new Date(value);
  if (Number.isNaN(targetDate.getTime())) {
    return null;
  }

  const today = startOfDay(new Date());
  const target = startOfDay(targetDate);
  return Math.round((target.getTime() - today.getTime()) / MS_IN_DAY);
};

export const getRelativeAvailabilityLabel = (value: string) => {
  const daysUntil = getDaysUntil(value);
  if (daysUntil === null) {
    return null;
  }

  if (daysUntil <= 0) {
    return 'сегодня';
  }

  if (daysUntil === 1) {
    return 'завтра';
  }

  if (daysUntil === 2) {
    return 'послезавтра';
  }

  return `через ${daysUntil} дн.`;
};

export const getUpcomingUrgency = (value: string) => {
  const daysUntil = getDaysUntil(value);
  if (daysUntil === null) {
    return 'planned' as const;
  }

  if (daysUntil <= 7) {
    return 'soon' as const;
  }

  return 'planned' as const;
};

export const getActiveUnavailability = (
  userId: string,
  periods: Array<{ user_id: string; status: string; started_at: string; ended_at: string }>
): UnavailabilityPeriodInfo | null => {
  const now = new Date();
  const activePeriod = periods.find((item) => {
    if (item.user_id !== userId) {
      return false;
    }

    const startedAt = new Date(item.started_at);
    const endedAt = new Date(item.ended_at);
    return startedAt <= now && endedAt >= now;
  });

  if (!activePeriod) {
    return null;
  }

  return {
    status: activePeriod.status,
    startedAt: activePeriod.started_at,
    endedAt: activePeriod.ended_at
  };
};

export const toPeriodInfo = (period: ResponsibilityUpcomingUnavailability): UnavailabilityPeriodInfo => ({
  status: period.status,
  startedAt: period.started_at,
  endedAt: period.ended_at
});

export const formatUnavailabilityRange = (period: UnavailabilityPeriodInfo) =>
  `${formatUnavailabilityDate(period.startedAt)} — ${formatUnavailabilityDate(period.endedAt)}`;

export const formatUnavailabilitySummary = (fullName: string, period: UnavailabilityPeriodInfo, prefix: string) => {
  const relativeLabel = getRelativeAvailabilityLabel(period.startedAt);
  const suffix = relativeLabel ? `, ${relativeLabel}` : '';
  const prefixPart = prefix ? `${prefix}: ` : '';
  return `${prefixPart}${fullName}, ${getUnavailabilityStatusLabel(period.status)} (${formatUnavailabilityRange(period)}${suffix})`;
};

export const getRequestOwnerWarningTooltip = ({
  activePeriod,
  upcomingPeriod,
}: {
  activePeriod: UnavailabilityPeriodInfo | null;
  upcomingPeriod: UnavailabilityPeriodInfo | null;
}) => {
  if (activePeriod) {
    return `Сотрудник сейчас недоступен. ${getUnavailabilityTooltip(activePeriod)}`;
  }

  if (upcomingPeriod) {
    return `Скоро будет недоступен. ${getUnavailabilityTooltip(upcomingPeriod)}`;
  }

  return null;
};

export const flattenEmployees = (nodes: ResponsibilityEmployeeNode[]): ResponsibilityEmployeeNode[] =>
  nodes.flatMap((node) => [node, ...flattenEmployees(node.children)]);

export const getNodeTotals = (statuses: ResponsibilityStatusCounter[]): StatusTotals =>
  statuses.reduce<StatusTotals>((acc, item) => {
    acc[item.status] = item.count;
    return acc;
  }, {});

export const sumTotals = (totals: StatusTotals): number => Object.values(totals).reduce((acc, count) => acc + count, 0);

export const mergeTotals = (left: StatusTotals, right: StatusTotals): StatusTotals => {
  const merged: StatusTotals = { ...left };
  for (const [status, count] of Object.entries(right)) {
    merged[status] = (merged[status] ?? 0) + count;
  }
  return merged;
};

export const collectDescendantTotals = (node: ResponsibilityEmployeeNode): StatusTotals => {
  return node.children.reduce<StatusTotals>((acc, child) => {
    const childOwn = getNodeTotals(child.statuses);
    const childDesc = collectDescendantTotals(child);
    return mergeTotals(acc, mergeTotals(childOwn, childDesc));
  }, {});
};

export const collectGlobalTotals = (nodes: ResponsibilityEmployeeNode[]): StatusTotals => {
  return nodes.reduce<StatusTotals>((acc, node) => {
    const own = getNodeTotals(node.statuses);
    const descendants = collectDescendantTotals(node);
    return mergeTotals(acc, mergeTotals(own, descendants));
  }, {});
};
