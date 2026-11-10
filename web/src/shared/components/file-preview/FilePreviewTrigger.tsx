import { lazy, Suspense, useState, type MouseEvent, type ReactNode } from 'react';
import { Dialog, DialogContent, Typography } from '@mui/material';
import type { FilePreviewSource } from '@shared/lib/files/preview';

const FilePreviewDialog = lazy(async () => ({ default: (await import('./FilePreviewDialog')).FilePreviewDialog }));

export const FilePreviewTrigger = ({ source, onDownload, children }: {
  source: FilePreviewSource;
  onDownload?: () => void | Promise<void>;
  children: (open: (event?: MouseEvent) => void) => ReactNode;
}) => {
  const [open, setOpen] = useState(false);
  return <>
    {children((event) => { event?.stopPropagation(); setOpen(true); })}
    {open ? <Suspense fallback={<Dialog open onClose={() => setOpen(false)} onClick={(event) => event.stopPropagation()}><DialogContent><Typography role="status">Открываем предпросмотр…</Typography></DialogContent></Dialog>}>
      <FilePreviewDialog source={source} onDownload={onDownload} onClose={() => setOpen(false)} />
    </Suspense> : null}
  </>;
};
