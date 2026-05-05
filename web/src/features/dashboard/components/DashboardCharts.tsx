import KeyboardArrowDownRoundedIcon from '@mui/icons-material/KeyboardArrowDownRounded';
import KeyboardArrowUpRoundedIcon from '@mui/icons-material/KeyboardArrowUpRounded';
import {
  Box,
  Card,
  CardContent,
  Stack,
  Tooltip,
  Typography
} from '@mui/material';
import { useState } from 'react';
import type { ResponsibilityEmployeeNode } from '@shared/api/users/getResponsibilityDashboard';
import { STATUS_LABELS, sumTotals, type StatusTotals } from './dashboardUtils';

export const ChevronUpIcon = () => (
  <KeyboardArrowUpRoundedIcon sx={{ fontSize: 20 }} />
);

export const ChevronDownIcon = () => (
  <KeyboardArrowDownRoundedIcon sx={{ fontSize: 20 }} />
);

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

export const SegmentedProgressBar = ({
  totals,
  statusColors,
  height = 24,
}: {
  totals: StatusTotals;
  statusColors: Record<string, string>;
  height?: number;
}) => {
  const normalizedEntries = Object.entries(totals)
    .filter(([, count]) => count > 0)
    .sort(([a], [b]) => (a > b ? 1 : -1));
  const total = sumTotals(totals);

  if (total === 0) {
    return (
      <Box
        sx={{
          height,
          borderRadius: 999,
          backgroundColor: 'rgba(47,111,214,0.14)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <Typography variant="caption" color="text.secondary">
          Нет активных заявок
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        borderRadius: 999,
        overflow: 'hidden',
        height,
        backgroundColor: 'rgba(47,111,214,0.16)',
        border: '1px solid rgba(47,111,214,0.18)',
        boxShadow: 'inset 0 1px 2px rgba(31,42,68,0.08)'
      }}
    >
      {normalizedEntries.map(([status, count]) => {
        const widthPercent = (count / total) * 100;
        const label = `${STATUS_LABELS[status] ?? status}: ${count}`;
        return (
          <Tooltip key={`${status}-${count}`} title={label} arrow>
            <Box
              sx={{
                width: `${widthPercent}%`,
                minWidth: 8,
                backgroundColor: statusColors[status] ?? '#64748b',
                transition: 'width 200ms ease'
              }}
            />
          </Tooltip>
        );
      })}
    </Box>
  );
};

export const CircularProcessChart = ({ totals, statusColors }: { totals: StatusTotals; statusColors: Record<string, string> }) => {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);
  const entries = Object.entries(totals)
    .filter(([, count]) => count > 0)
    .sort(([a], [b]) => (a > b ? 1 : -1));
  const total = sumTotals(totals);

  if (total === 0) {
    return (
      <Card sx={{ borderRadius: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1, fontWeight: 700 }}>
            Общая диаграмма процесса заявок
          </Typography>
          <Typography color="text.secondary">Нет активных заявок для отображения диаграммы.</Typography>
        </CardContent>
      </Card>
    );
  }

  let currentAngle = -90;
  const pieSegments = entries.map(([status, count]) => {
    const percent = (count / total) * 100;
    const sweep = (count / total) * 360;
    const endAngle = currentAngle + sweep;
    const segment = {
      status,
      count,
      percent,
      color: statusColors[status] ?? '#64748b',
      startAngle: currentAngle,
      endAngle
    };
    currentAngle = endAngle;
    return segment;
  });

  return (
    <Card
      sx={{
        borderRadius: 2,
        ackground: 'linear-gradient(135deg, rgba(231,240,255,0.92), rgba(255,255,255,0.98))',
        border: '1px solid',
        borderColor: 'divider'
      }}
    >
      <CardContent>
        <Typography variant="h6" sx={{ mb: 0.5, fontWeight: 700 }}>
          Общая диаграмма процесса заявок
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Круговая диаграмма всех активных заявок по этапам процесса.
        </Typography>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '128px minmax(0, 1fr)', md: '220px minmax(0, 1fr)' },
            gap: { xs: 1.25, md: 2 },
            alignItems: 'center'
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Tooltip open={Boolean(activeTooltip)} title={activeTooltip ?? ''} disableFocusListener disableTouchListener placement="top">
              <Box
                sx={{
                  position: 'relative',
                  width: { xs: 128, md: 180 },
                  height: { xs: 128, md: 180 },
                  borderRadius: '50%',
                  boxShadow: 'inset 0 0 0 1px rgba(47,111,214,0.16), 0 10px 24px rgba(31,42,68,0.12)'
                }}
              >
                <Box component="svg" viewBox="0 0 200 200" sx={{ width: '100%', height: '100%' }}>
                  {pieSegments.map((segment) => (
                    <path
                      key={`process-sector-${segment.status}`}
                      d={describeSectorPath(100, 100, 88, segment.startAngle, segment.endAngle)}
                      fill={segment.color}
                      stroke="#ffffff"
                      strokeWidth={2}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() =>
                        setActiveTooltip(
                          `${STATUS_LABELS[segment.status] ?? segment.status}: ${segment.count} · ${Math.round(segment.percent * 10) / 10}%`
                        )
                      }
                      onMouseLeave={() => setActiveTooltip(null)}
                      onClick={() =>
                        setActiveTooltip(
                          `${STATUS_LABELS[segment.status] ?? segment.status}: ${segment.count} · ${Math.round(segment.percent * 10) / 10}%`
                        )
                      }
                    />
                  ))}
                </Box>
              <Box
                sx={{
                  position: 'absolute',
                  inset: { xs: 16, md: 20 },
                  borderRadius: '50%',
                  backgroundColor: 'background.paper',
                  boxShadow: '0 0 0 1px rgba(47,111,214,0.10)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center'
                }}
              >
                <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', md: 'block' } }}>
                  Всего в работе
                </Typography>
                <Typography variant="h4" fontWeight={800}>
                  {total}
                </Typography>
              </Box>
              </Box>
            </Tooltip>
          </Box>

          <Stack spacing={{ xs: 0.8, md: 1.2 }}>
            {entries.map(([status, count]) => {
              const percent = Math.round((count / total) * 1000) / 10;
              return (
                <Card key={`process-${status}`} variant="outlined" sx={{ borderRadius: 2.5 }}>
                  <CardContent sx={{ py: { xs: 0.75, md: 1.25 }, px: { xs: 1.1, md: 2 }, '&:last-child': { pb: { xs: 0.75, md: 1.25 } } }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={0.75}>
                      <Stack direction="row" spacing={0.75} alignItems="center" sx={{ minWidth: 0, flex: 1 }}>
                        <Box
                          sx={{
                            width: 10,
                            height: 10,
                            borderRadius: '50%',
                            backgroundColor: statusColors[status] ?? '#64748b',
                            flexShrink: 0
                          }}
                        />
                        <Typography variant="body2" fontWeight={600} noWrap>
                          {STATUS_LABELS[status] ?? status}
                        </Typography>
                      </Stack>
                      <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'nowrap', flexShrink: 0 }}>
                        {count} · {percent}%
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>
              );
            })}
          </Stack>
        </Box>
      </CardContent>
    </Card>
  );
};

export const EmployeeWorkloadChart = ({
  employees,
  workloadColors
}: {
  employees: ResponsibilityEmployeeNode[];
  workloadColors: string[];
}) => {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);
  const entries = employees
    .map((employee) => ({
      userId: employee.user_id,
      label: employee.full_name || employee.user_id,
      count: employee.in_progress_total
    }))
    .filter((entry) => entry.count > 0)
    .sort((a, b) => b.count - a.count);
  const total = entries.reduce((acc, entry) => acc + entry.count, 0);

  if (total === 0) {
    return (
      <Card sx={{ borderRadius: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1, fontWeight: 700 }}>
            Соотношение занятости сотрудников
          </Typography>
          <Typography color="text.secondary">Нет активных заявок для отображения диаграммы.</Typography>
        </CardContent>
      </Card>
    );
  }

  let currentAngle = -90;
  const pieSegments = entries.map((entry, index) => {
    const percent = (entry.count / total) * 100;
    const sweep = (entry.count / total) * 360;
    const endAngle = currentAngle + sweep;
    const segment = {
      ...entry,
      percent,
      color: workloadColors[index % workloadColors.length] ?? '#64748b',
      startAngle: currentAngle,
      endAngle
    };
    currentAngle = endAngle;
    return segment;
  });

  return (
    <Card
      sx={{
        borderRadius: 2,
        background: 'linear-gradient(135deg, rgba(231,240,255,0.92), rgba(255,255,255,0.98))',
        border: '1px solid',
        borderColor: 'divider'
      }}
    >
      <CardContent>
        <Typography variant="h6" sx={{ mb: 0.5, fontWeight: 700 }}>
          Соотношение занятости сотрудников
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Круговая диаграмма распределения активных заявок между сотрудниками.
        </Typography>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '128px minmax(0, 1fr)', md: '220px minmax(0, 1fr)' },
            gap: { xs: 1.25, md: 2 },
            alignItems: 'center'
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Tooltip open={Boolean(activeTooltip)} title={activeTooltip ?? ''} disableFocusListener disableTouchListener placement="top">
              <Box
                sx={{
                  position: 'relative',
                  width: { xs: 128, md: 180 },
                  height: { xs: 128, md: 180 },
                  borderRadius: '50%',
                  boxShadow: 'inset 0 0 0 1px rgba(47,111,214,0.16), 0 10px 24px rgba(31,42,68,0.12)'
                }}
              >
                <Box component="svg" viewBox="0 0 200 200" sx={{ width: '100%', height: '100%' }}>
                  {pieSegments.map((segment) => (
                    <path
                      key={`workload-sector-${segment.userId}`}
                      d={describeSectorPath(100, 100, 88, segment.startAngle, segment.endAngle)}
                      fill={segment.color}
                      stroke="#ffffff"
                      strokeWidth={2}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() =>
                        setActiveTooltip(`${segment.label}: ${segment.count} · ${Math.round(segment.percent * 10) / 10}%`)
                      }
                      onMouseLeave={() => setActiveTooltip(null)}
                      onClick={() =>
                        setActiveTooltip(`${segment.label}: ${segment.count} · ${Math.round(segment.percent * 10) / 10}%`)
                      }
                    />
                  ))}
                </Box>
              <Box
                sx={{
                  position: 'absolute',
                  inset: { xs: 16, md: 20 },
                  borderRadius: '50%',
                  backgroundColor: 'background.paper',
                  boxShadow: '0 0 0 1px rgba(47,111,214,0.10)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center'
                }}
              >
                <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', md: 'block' } }}>
                  Всего в работе
                </Typography>
                <Typography variant="h4" fontWeight={800}>
                  {total}
                </Typography>
              </Box>
              </Box>
            </Tooltip>
          </Box>

          <Stack spacing={{ xs: 0.8, md: 1.2 }}>
            {entries.map((entry, index) => {
              const percent = Math.round((entry.count / total) * 1000) / 10;
              return (
                <Card key={`workload-${entry.userId}`} variant="outlined" sx={{ borderRadius: 2.5 }}>
                  <CardContent sx={{ py: { xs: 0.75, md: 1.25 }, px: { xs: 1.1, md: 2 }, '&:last-child': { pb: { xs: 0.75, md: 1.25 } } }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={0.75}>
                      <Stack direction="row" spacing={0.75} alignItems="center" sx={{ minWidth: 0, flex: 1 }}>
                        <Box
                          sx={{
                            width: 10,
                            height: 10,
                            borderRadius: '50%',
                            backgroundColor: workloadColors[index % workloadColors.length] ?? '#64748b',
                            flexShrink: 0
                          }}
                        />
                        <Typography
                          variant="body2"
                          fontWeight={600}
                          sx={{
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                            lineHeight: 1.2
                          }}
                        >
                          {entry.label}
                        </Typography>
                      </Stack>
                      <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'nowrap', flexShrink: 0 }}>
                        {entry.count} · {percent}%
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>
              );
            })}
          </Stack>
        </Box>
      </CardContent>
    </Card>
  );
};
