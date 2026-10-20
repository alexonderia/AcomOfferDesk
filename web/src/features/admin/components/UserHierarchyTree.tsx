import { Box, Chip, Stack, Typography } from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import type { UnitNode } from '@shared/api/units';
import type { UserHierarchy } from '@shared/api/users/getUserHierarchy';
import { buildUnitPeopleTree } from '@shared/lib/hierarchy/buildUnitPeopleTree';
import { UnitOrgReadonlyList } from '@features/unit-hierarchy/ui/UnitOrgReadonlyList';
import type { HierarchyPersonTone, HierarchyPersonVisual } from '@shared/ui/hierarchy/hierarchyPersonUtils';
import {
  buildUnitRelationKinds,
  buildUserHierarchyDisplayUnits,
  collectUniqueStaff,
} from './userHierarchyTreeUtils';

export const UserHierarchyTree = ({
  hierarchy,
  unitsTree,
}: {
  hierarchy: UserHierarchy;
  unitsTree: UnitNode[];
}) => {
  const theme = useTheme();
  const displayUnits = buildUserHierarchyDisplayUnits(hierarchy, unitsTree);

  if (displayUnits.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        Подходящих подразделений для отображения не найдено.
      </Typography>
    );
  }

  return (
    <Stack spacing={1}>
      {displayUnits.map(({ departmentName, unit }) => (
        (() => {
          const roots = buildUnitPeopleTree(unit);
          const relationKinds = buildUnitRelationKinds({
            roots,
            selectedUserId: hierarchy.user.userId,
          });

          const resolveRelationTooltip = (person: HierarchyPersonVisual) => {
            const relation = relationKinds.get(person.userId);
            if (relation === 'self') {
              return 'Выбранный сотрудник';
            }
            if (relation === 'manager') {
              return 'Руководитель выбранного сотрудника';
            }
            if (relation === 'subordinate') {
              return 'Подчинённый выбранного сотрудника';
            }
            return null;
          };

          const resolveRelationTone = (person: HierarchyPersonVisual): HierarchyPersonTone =>
            relationKinds.get(person.userId) ?? 'default';

          const resolveRelationHighlight = (person: HierarchyPersonVisual) =>
            relationKinds.get(person.userId) === 'self';

          return (
            <Box
              key={unit.unit_id}
              sx={{
                border: '1px solid',
                borderColor: alpha(theme.palette.primary.main, 0.14),
                borderRadius: `${theme.acomShape.controlRadius}px`,
                overflow: 'hidden',
                backgroundColor: theme.palette.background.paper,
                boxShadow: `0 2px 8px ${alpha(theme.palette.common.black, 0.035)}`,
              }}
            >
              <Box
                sx={{
                  px: 1.25,
                  py: 0.95,
                  bgcolor: 'brand.softSection',
                  borderBottom: '1px solid',
                  borderColor: alpha(theme.palette.primary.main, 0.12),
                }}
              >
                <Typography sx={{ fontSize: 14, fontWeight: 700, overflowWrap: 'anywhere' }}>
                  {unit.name}
                </Typography>
                {departmentName !== unit.name ? (
                  <Typography sx={{ fontSize: 12, color: 'text.secondary', overflowWrap: 'anywhere' }}>
                    {departmentName}
                  </Typography>
                ) : null}
                <Stack direction="row" spacing={0.7} flexWrap="wrap" useFlexGap sx={{ mt: 0.75 }}>
                  <Chip
                    label={`${collectUniqueStaff(unit).length} Сотрудники`}
                    size="small"
                    sx={{
                      height: 24,
                      bgcolor: alpha(theme.palette.success.main, 0.06),
                      color: theme.palette.text.secondary,
                      border: '1px solid',
                      borderColor: alpha(theme.palette.success.main, 0.22),
                    }}
                  />
                  <Chip
                    label={`${unit.children.length} Группы`}
                    size="small"
                    sx={{
                      height: 24,
                      bgcolor: alpha(theme.palette.primary.main, 0.05),
                      color: theme.palette.text.secondary,
                      border: '1px solid',
                      borderColor: alpha(theme.palette.primary.main, 0.18),
                    }}
                  />
                </Stack>
              </Box>

              <Box sx={{ p: 1 }}>
                <UnitOrgReadonlyList
                  highlightRoots={false}
                  resolveHighlight={resolveRelationHighlight}
                  resolveTone={resolveRelationTone}
                  resolveTooltipTitle={resolveRelationTooltip}
                  units={[unit]}
                />
              </Box>
            </Box>
          );
        })()
      ))}
    </Stack>
  );
};
