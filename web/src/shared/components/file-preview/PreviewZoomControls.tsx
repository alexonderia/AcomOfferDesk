import FitScreenOutlined from '@mui/icons-material/FitScreenOutlined';
import ZoomInOutlined from '@mui/icons-material/ZoomInOutlined';
import ZoomOutOutlined from '@mui/icons-material/ZoomOutOutlined';
import { Button, IconButton, Stack, Tooltip, Typography } from '@mui/material';

export const PreviewZoomControls = ({ zoom, onChange, disabled }: {
  zoom: number; onChange: (zoom: number) => void; disabled: boolean;
}) => <Stack direction="row" spacing={0.5} alignItems="center" flexWrap="wrap" useFlexGap role="group" aria-label="Масштаб предпросмотра" sx={{ mt: 1 }}>
  <Tooltip title="Уменьшить"><span><IconButton size="small" aria-label="Уменьшить" disabled={disabled || zoom <= 0.25} onClick={() => onChange(Math.max(0.25, zoom - 0.25))}><ZoomOutOutlined /></IconButton></span></Tooltip>
  <Typography variant="body2" aria-live="polite" sx={{ minWidth: 48, textAlign: 'center' }}>{Math.round(zoom * 100)}%</Typography>
  <Tooltip title="Увеличить"><span><IconButton size="small" aria-label="Увеличить" disabled={disabled || zoom >= 4} onClick={() => onChange(Math.min(4, zoom + 0.25))}><ZoomInOutlined /></IconButton></span></Tooltip>
  <Button size="small" startIcon={<FitScreenOutlined />} disabled={disabled} onClick={() => onChange(1)}>По высоте окна</Button>
</Stack>;
