import { Box } from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { UnitNode } from '@shared/api/units';
import { UnitOrgNode } from './UnitOrgNode';
import { hierarchyCanvasBackground, hierarchyPageColors } from './unitHierarchyStyles';

type UnitOrgChartProps = {
  onCreateChild?: ((unit: UnitNode) => void) | undefined;
  onDeactivate: (unit: UnitNode) => void;
  onOpenMemberDialog?: ((unit: UnitNode) => void) | undefined;
  onOpenUnitDetails?: ((unit: UnitNode) => void) | undefined;
  onRename: (unit: UnitNode) => void;
  showMembers?: boolean;
  showPrimaryActions?: boolean;
  tree: UnitNode[];
};

export const UnitOrgChart = ({
  onCreateChild,
  onDeactivate,
  onOpenMemberDialog,
  onOpenUnitDetails,
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
      backgroundImage: hierarchyCanvasBackground,
      border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
      boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.75)',
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
          gap: { xs: 2.25, md: 3.25 },
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
            onOpenMemberDialog={onOpenMemberDialog}
            onOpenUnitDetails={onOpenUnitDetails}
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
