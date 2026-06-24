import PersonRemoveAlt1OutlinedIcon from '@mui/icons-material/PersonRemoveAlt1Outlined';
import { Box, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { UnitMember } from '@shared/api/units';
import {
  getMemberAccentColor,
  getMemberDisplayName,
  hierarchyPageColors,
  isPlaceholderPersonName,
  statusLabelByCode,
} from './unitHierarchyStyles';

type OrgUserCardProps = {
  canManageMembers: boolean;
  member: UnitMember;
  onDelete?: () => void;
  unitLabel: string;
};

export const OrgUserCard = ({
  canManageMembers,
  member,
  onDelete,
  unitLabel,
}: OrgUserCardProps) => {
  const displayName = getMemberDisplayName(member);
  const isPlaceholder = isPlaceholderPersonName(displayName);
  const accentColor = getMemberAccentColor(member.role_name);

  return (
    <Box
      sx={{
        width: 172,
        minHeight: 104,
        borderRadius: 2.2,
        border: `1px solid ${
          isPlaceholder ? alpha(hierarchyPageColors.softPink, 0.55) : alpha(hierarchyPageColors.cardBorder, 0.95)
        }`,
        backgroundColor: '#ffffff',
        boxShadow: '0 1px 3px rgba(15, 23, 42, 0.06)',
        px: 1.1,
        py: 1,
      }}
    >
      <Stack spacing={0.75} sx={{ height: '100%' }}>
        <Stack direction="row" spacing={0.5} alignItems="flex-start" justifyContent="space-between">
          <Box minWidth={0}>
            <Typography
              sx={{
                color: isPlaceholder ? hierarchyPageColors.softPink : hierarchyPageColors.textPrimary,
                fontSize: 12.2,
                fontWeight: 700,
                lineHeight: 1.2,
                overflowWrap: 'anywhere',
              }}
            >
              {displayName}
            </Typography>
          </Box>

          {canManageMembers && onDelete ? (
            <Tooltip title="Удалить участника">
              <IconButton size="small" onClick={onDelete} sx={{ mt: -0.35, mr: -0.45 }}>
                <PersonRemoveAlt1OutlinedIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
          ) : null}
        </Stack>

        <Typography
          variant="body2"
          sx={{
            color: hierarchyPageColors.textPrimary,
            fontSize: 11,
            lineHeight: 1.22,
          }}
        >
          {member.role_name}
        </Typography>

        <Typography
          variant="caption"
          sx={{
            color: alpha(hierarchyPageColors.textSecondary, 0.84),
            fontSize: 9.8,
            lineHeight: 1.2,
          }}
        >
          {unitLabel}
        </Typography>

        <Box sx={{ mt: 'auto', pt: 0.3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Stack direction="row" spacing={0.55} alignItems="center">
            <Box
              sx={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                backgroundColor: accentColor,
                flexShrink: 0,
              }}
            />
            <Typography
              variant="caption"
              sx={{
                color: alpha(hierarchyPageColors.textSecondary, 0.92),
                fontSize: 10,
              }}
            >
              {statusLabelByCode[member.status] ?? member.status}
            </Typography>
          </Stack>

          <Typography
            variant="caption"
            sx={{
              color: alpha(hierarchyPageColors.textSecondary, 0.72),
              fontSize: 10,
            }}
          >
            {member.user_id}
          </Typography>
        </Box>
      </Stack>
    </Box>
  );
};
