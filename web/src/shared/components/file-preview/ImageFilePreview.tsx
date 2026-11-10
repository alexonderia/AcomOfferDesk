import { Box } from '@mui/material';
import { useRef, useState } from 'react';
import { usePreviewSize } from './usePreviewSize';

export const ImageFilePreview = ({ url, name, zoom, onError }: {
  url: string; name: string; zoom: number; onError: () => void;
}) => {
  const container = useRef<HTMLDivElement>(null);
  const size = usePreviewSize(container);
  const [naturalSize, setNaturalSize] = useState<{ width: number; height: number } | null>(null);
  const scale = naturalSize ? Math.min(size.width / naturalSize.width, size.height / naturalSize.height) * zoom : 1;
  return <Box ref={container} role="region" aria-label="Область просмотра изображения" sx={{ flex: 1, minHeight: 0, minWidth: 0, overflow: 'auto', p: 1 }}>
    <Box sx={{ minWidth: '100%', minHeight: '100%', width: 'max-content', height: 'max-content', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Box component="img" src={url} alt={name}
        onLoad={(event) => setNaturalSize({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })}
        onError={onError}
        sx={{ display: 'block', flexShrink: 0, maxWidth: 'none', width: naturalSize ? `${naturalSize.width * scale}px` : '1px', height: naturalSize ? `${naturalSize.height * scale}px` : '1px', visibility: naturalSize ? 'visible' : 'hidden' }} />
    </Box>
  </Box>;
};
