import { Box } from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { UnitMember, UnitNode } from '@shared/api/units';
import { UnitOrgNode } from './UnitOrgNode';
import { hierarchyPageColors } from './unitHierarchyStyles';

type UnitOrgChartProps = {
  onCreateChild?: ((unit: UnitNode) => void) | undefined;
  onDeactivate: (unit: UnitNode) => void;
  onDeleteMember: (unit: UnitNode, member: UnitMember) => void;
  onOpenMemberDialog?: ((unit: UnitNode) => void) | undefined;
  onRename: (unit: UnitNode) => void;
  showMembers?: boolean;
  showPrimaryActions?: boolean;
  tree: UnitNode[];
};

export const UnitOrgChart = ({
  onCreateChild,
  onDeactivate,
  onDeleteMember,
  onOpenMemberDialog,
  onRename,
  showMembers = true,
  showPrimaryActions = true,
  tree,
}: UnitOrgChartProps) => (
  <Box
    sx={{
      overflowX: 'auto',
      overflowY: 'hidden',
      borderRadius: 3.5,
      bgcolor: hierarchyPageColors.canvas,
      border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
      px: { xs: 1, md: 1.75 },
      py: { xs: 1.5, md: 2.1 },
    }}
  >
    <Box
      sx={{
        width: 'max-content',
        minWidth: '100%',
        display: 'flex',
        justifyContent: 'center',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          gap: { xs: 2, md: 2.5 },
          alignItems: 'flex-start',
          width: 'max-content',
        }}
      >
      {tree.map((unit) => (
        <Box
          key={unit.unit_id}
          sx={{
            width: 'max-content',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'flex-start',
          }}
        >
          <UnitOrgNode
            depth={0}
            onCreateChild={onCreateChild}
            onDeactivate={onDeactivate}
            onDeleteMember={onDeleteMember}
            onOpenMemberDialog={onOpenMemberDialog}
            onRename={onRename}
            showMembers={showMembers}
            showPrimaryActions={showPrimaryActions}
            unit={unit}
          />
        </Box>
      ))}
      </Box>
    </Box>
  </Box>
);
