import { Alert, Box, Button, CircularProgress, Stack, Typography } from '@mui/material';
import { useEffect, useRef, useState } from 'react';
import type { PDFDocumentLoadingTask, PDFDocumentProxy } from 'pdfjs-dist';
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { usePreviewSize } from './usePreviewSize';

export const PdfFilePreview = ({ blob, zoom }: { blob: Blob; zoom: number }) => {
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const container = useRef<HTMLDivElement>(null);
  const { width, height } = usePreviewSize(container);

  useEffect(() => {
    let active = true;
    let task: PDFDocumentLoadingTask | undefined;
    const load = async () => {
      try {
        const [pdfjs, buffer] = await Promise.all([import('pdfjs-dist'), blob.arrayBuffer()]);
        if (!active) return;
        pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;
        task = pdfjs.getDocument({ data: buffer, useSystemFonts: true, enableXfa: false,
          cMapUrl: '/pdfjs/cmaps/', cMapPacked: true, standardFontDataUrl: '/pdfjs/standard_fonts/', wasmUrl: '/pdfjs/wasm/' });
        const pdf = await task.promise;
        if (active) { setDocument(pdf); setPageNumber(1); setBusy(false); }
      } catch (e) {
        if (active) {
          setError(e instanceof Error && e.name === 'PasswordException' ? 'PDF защищён паролем. Скачайте его для просмотра.' : 'Не удалось открыть PDF. Файл может быть повреждён.');
          setBusy(false);
        }
      }
    };
    void load();
    return () => { active = false; if (task) void task.destroy().catch(() => {}); };
  }, [blob]);

  return <Stack spacing={1.5} sx={{ flex: 1, minHeight: 0, minWidth: 0 }}>
    {busy ? <Stack direction="row" spacing={1}><CircularProgress size={20} /><Typography role="status">Открываем PDF…</Typography></Stack> : null}
    {error ? <Alert severity="error">{error}</Alert> : null}
    {document ? <Stack direction="row" spacing={1} alignItems="center" justifyContent="center" flexWrap="wrap" useFlexGap sx={{ flexShrink: 0 }}>
      <Button disabled={pageNumber <= 1} onClick={() => setPageNumber((value) => value - 1)}>Предыдущая страница</Button>
      <Typography>Страница {pageNumber} из {document.numPages}</Typography>
      <Button disabled={pageNumber >= document.numPages} onClick={() => setPageNumber((value) => value + 1)}>Следующая страница</Button>
    </Stack> : null}
    <Box ref={container} role="region" aria-label="Область просмотра PDF" sx={{ flex: 1, width: '100%', minWidth: 0, minHeight: 0, overflow: 'auto', p: 1 }}>
      {document ? <PdfPage key={`${pageNumber}-${width}-${height}-${zoom}`} document={document} pageNumber={pageNumber} width={width} height={height} zoom={zoom} /> : null}
    </Box>
  </Stack>;
};

// A fresh canvas per page/size avoids rendering two PDF operations into one canvas.
const PdfPage = ({ document, pageNumber, width, height, zoom }: { document: PDFDocumentProxy; pageNumber: number; width: number; height: number; zoom: number }) => {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(true);
  useEffect(() => {
    let active = true;
    let cancel: (() => void) | undefined;
    const render = async () => {
      try {
        const page = await document.getPage(pageNumber);
        if (!active || !canvas.current) return;
        const original = page.getViewport({ scale: 1 });
        const scale = Math.min(width / original.width, height / original.height) * zoom;
        const viewport = page.getViewport({ scale });
        const ratio = Math.min(window.devicePixelRatio || 1, 2, Math.sqrt(8_000_000 / (viewport.width * viewport.height)));
        canvas.current.width = Math.ceil(viewport.width * ratio);
        canvas.current.height = Math.ceil(viewport.height * ratio);
        canvas.current.style.width = `${viewport.width}px`;
        canvas.current.style.height = `${viewport.height}px`;
        const task = page.render({ canvas: canvas.current, viewport, transform: ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0] });
        cancel = () => task.cancel();
        await task.promise;
        if (active) setBusy(false);
      } catch { if (active) { setError(true); setBusy(false); } }
    };
    void render();
    return () => { active = false; cancel?.(); };
  }, [document, pageNumber, width, height, zoom]);
  return <Stack spacing={1} alignItems="center" justifyContent="center" sx={{ minWidth: '100%', minHeight: '100%', width: 'max-content', height: 'max-content' }}>
    {busy ? <Typography role="status">Отображаем страницу…</Typography> : null}
    {error ? <Alert severity="error">Не удалось отобразить страницу PDF. Скачайте исходный файл.</Alert> : null}
    <canvas ref={canvas} aria-label={`Страница PDF ${pageNumber}`} role="img" style={{ flexShrink: 0, display: error ? 'none' : 'block' }} />
  </Stack>;
};
