import CenterFocusStrongRoundedIcon from '@mui/icons-material/CenterFocusStrongRounded';
import ZoomInRoundedIcon from '@mui/icons-material/ZoomInRounded';
import ZoomOutRoundedIcon from '@mui/icons-material/ZoomOutRounded';
import { Box, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { memo, useRef, useState, type CSSProperties, type MouseEvent as ReactMouseEvent } from 'react';
import type { UnitNode } from '@shared/api/units';
import { UnitOrgNode } from './UnitOrgNode';
import { hierarchyCanvasBackground, hierarchyPageColors, outlinedIconButtonSx } from './unitHierarchyStyles';

type UnitOrgChartProps = {
  fillHeight?: boolean;
  onDelete: (unit: UnitNode) => void;
  onOpenCreateChildDialog?: ((unit: UnitNode) => void) | undefined;
  onMoveMember?: ((unit: UnitNode, member: UnitNode['members'][number]) => void) | undefined;
  onOpenMemberDialog?: ((unit: UnitNode) => void) | undefined;
  onOpenUnitDetails?: ((unit: UnitNode) => void) | undefined;
  onRemoveMember?: ((unit: UnitNode, member: UnitNode['members'][number]) => void) | undefined;
  showMembers?: boolean;
  showPrimaryActions?: boolean;
  showZoomControls?: boolean;
  tree: UnitNode[];
};

const MIN_ZOOM = 0.4;
const MAX_ZOOM = 1.4;
const ZOOM_STEP = 0.1;
const DEFAULT_ZOOM = 0.8;
const DRAG_THRESHOLD = 5;

const clampZoom = (value: number) => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Math.round(value * 100) / 100));

export const UnitOrgChart = memo(({
  fillHeight = false,
  onDelete,
  onOpenCreateChildDialog,
  onMoveMember,
  onOpenMemberDialog,
  onOpenUnitDetails,
  onRemoveMember,
  showMembers = true,
  showPrimaryActions = true,
  showZoomControls = true,
  tree,
}: UnitOrgChartProps) => {
  const [zoom, setZoom] = useState(DEFAULT_ZOOM);
  const [isPanning, setIsPanning] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const panRef = useRef({ down: false, dragging: false, startX: 0, startY: 0, scrollLeft: 0, scrollTop: 0 });
  const draggedRef = useRef(false);

  const handleMouseDown = (event: ReactMouseEvent<HTMLDivElement>) => {
    if (event.button !== 0) {
      return;
    }
    const element = scrollRef.current;
    if (!element) {
      return;
    }
    draggedRef.current = false;
    panRef.current = {
      down: true,
      dragging: false,
      startX: event.clientX,
      startY: event.clientY,
      scrollLeft: element.scrollLeft,
      scrollTop: element.scrollTop,
    };
  };

  const handleMouseMove = (event: ReactMouseEvent<HTMLDivElement>) => {
    const state = panRef.current;
    if (!state.down) {
      return;
    }
    const dx = event.clientX - state.startX;
    const dy = event.clientY - state.startY;
    if (!state.dragging && Math.hypot(dx, dy) < DRAG_THRESHOLD) {
      return;
    }
    const element = scrollRef.current;
    if (!element) {
      return;
    }
    state.dragging = true;
    draggedRef.current = true;
    setIsPanning(true);
    element.scrollLeft = state.scrollLeft - dx;
    element.scrollTop = state.scrollTop - dy;
    event.preventDefault();
  };

  const endPan = () => {
    if (panRef.current.down) {
      panRef.current.down = false;
      panRef.current.dragging = false;
      setIsPanning(false);
    }
  };

  // Suppress the click that terminates a pan gesture so cards don't open while dragging.
  const handleClickCapture = (event: ReactMouseEvent<HTMLDivElement>) => {
    if (draggedRef.current) {
      event.preventDefault();
      event.stopPropagation();
      draggedRef.current = false;
    }
  };

  return (
    <Box sx={{ position: 'relative' }}>
      {showZoomControls ? (
        <Stack
          direction="row"
          spacing={0.25}
          alignItems="center"
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            zIndex: 6,
            borderRadius: 2,
            border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
            backgroundColor: alpha('#ffffff', 0.92),
            backdropFilter: 'blur(4px)',
            boxShadow: hierarchyPageColors.shadow,
            px: 0.4,
            py: 0.2,
          }}
        >
          <Tooltip title="Отдалить">
            <span>
              <IconButton
                size="small"
                disabled={zoom <= MIN_ZOOM}
                onClick={() => setZoom((current) => clampZoom(current - ZOOM_STEP))}
                aria-label="Отдалить граф"
                sx={outlinedIconButtonSx}
              >
                <ZoomOutRoundedIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </span>
          </Tooltip>
          <Typography sx={{ minWidth: 38, textAlign: 'center', fontSize: 12, fontWeight: 700, color: hierarchyPageColors.textSecondary }}>
            {Math.round(zoom * 100)}%
          </Typography>
          <Tooltip title="Приблизить">
            <span>
              <IconButton
                size="small"
                disabled={zoom >= MAX_ZOOM}
                onClick={() => setZoom((current) => clampZoom(current + ZOOM_STEP))}
                aria-label="Приблизить граф"
                sx={outlinedIconButtonSx}
              >
                <ZoomInRoundedIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title="Сбросить масштаб">
            <IconButton size="small" onClick={() => setZoom(DEFAULT_ZOOM)} aria-label="Сбросить масштаб" sx={outlinedIconButtonSx}>
              <CenterFocusStrongRoundedIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
        </Stack>
      ) : null}

      <Box
        ref={scrollRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={endPan}
        onMouseLeave={endPan}
        onClickCapture={handleClickCapture}
        sx={{
          overflow: 'auto',
          height: fillHeight ? { xs: 'calc(100vh - 150px)', md: 'calc(100vh - 128px)' } : undefined,
          maxHeight: fillHeight ? undefined : { xs: '62vh', md: '72vh' },
          borderRadius: 2.5,
          bgcolor: hierarchyPageColors.canvas,
          backgroundImage: hierarchyCanvasBackground,
          border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
          px: { xs: 1, md: 1.75 },
          py: { xs: 1.5, md: 2.1 },
          cursor: isPanning ? 'grabbing' : 'grab',
          userSelect: isPanning ? 'none' : 'auto',
        }}
      >
        <Box
          style={{ zoom } as CSSProperties}
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
                  onDelete={onDelete}
                  onOpenCreateChildDialog={onOpenCreateChildDialog}
                  onMoveMember={onMoveMember}
                  onOpenMemberDialog={onOpenMemberDialog}
                  onOpenUnitDetails={onOpenUnitDetails}
                  onRemoveMember={onRemoveMember}
                  showMembers={showMembers}
                  showPrimaryActions={showPrimaryActions}
                  unit={unit}
                />
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
    </Box>
  );
});

UnitOrgChart.displayName = 'UnitOrgChart';
