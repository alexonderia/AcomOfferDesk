import type { ReactNode } from 'react';
import { Box, Stack, Tooltip, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { HierarchyPersonAvatar } from './HierarchyPersonAvatar';
import {
  getHierarchyPersonRowSx,
  getHierarchyStatusColor,
} from './hierarchyThemeStyles';
import {
  getPersonDisplayName,
  type HierarchyPersonTone,
  hierarchyStatusLabelByCode,
  type HierarchyPersonVisual,
} from './hierarchyPersonUtils';

type HierarchyViewPersonRowProps = {
  endAdornment?: ReactNode;
  highlight?: boolean;
  meta?: ReactNode;
  person: HierarchyPersonVisual;
  roleSuffix?: string | null;
  tone?: HierarchyPersonTone;
  tooltipTitle?: ReactNode;
};

export const HierarchyViewPersonRow = ({
  endAdornment,
  highlight = false,
  meta,
  person,
  roleSuffix,
  tone = 'default',
  tooltipTitle,
}: HierarchyViewPersonRowProps) => {
  const theme = useTheme();
  const displayName = getPersonDisplayName(person.fullName, person.userId);
  const status = person.status ?? 'active';
  const statusColor = getHierarchyStatusColor(theme, status);
  const roleLine = roleSuffix ? `${person.roleName}${roleSuffix}` : person.roleName;

  const row = (
    <Box sx={getHierarchyPersonRowSx(theme, highlight, tone)}>
      <HierarchyPersonAvatar highlight={highlight} person={person} tone={tone} />

      <Box sx={{ minWidth: 0, flex: 1 }}>
        <Stack direction="row" spacing={0.6} alignItems="center" sx={{ minWidth: 0 }}>
          {meta}
          <Typography
            sx={{
              fontSize: theme.typography.body1.fontSize,
              fontWeight: highlight ? 700 : 600,
              lineHeight: 1.25,
              color: 'text.primary',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              minWidth: 0,
            }}
          >
            {displayName}
          </Typography>
        </Stack>
        <Stack direction="row" spacing={0.55} alignItems="center" sx={{ mt: 0.2, minWidth: 0 }}>
          <Tooltip title={hierarchyStatusLabelByCode[status] ?? status}>
            <Box sx={{ width: 7, height: 7, borderRadius: '50%', bgcolor: statusColor, flexShrink: 0 }} />
          </Tooltip>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              lineHeight: 1.2,
            }}
          >
            {roleLine}
          </Typography>
        </Stack>
      </Box>

      {endAdornment ? <Box sx={{ flexShrink: 0 }}>{endAdornment}</Box> : null}
    </Box>
  );

  if (!tooltipTitle) {
    return row;
  }

  return (
    <Tooltip title={tooltipTitle}>
      {row}
    </Tooltip>
  );
};
