import CloseOutlined from '@mui/icons-material/CloseOutlined';
import DownloadOutlined from '@mui/icons-material/DownloadOutlined';
import { Alert, Box, Button, CircularProgress, Dialog, DialogContent, DialogTitle, IconButton, MenuItem, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { lazy, Suspense, useEffect, useState } from 'react';
import { downloadFile } from '@shared/api/fileDownload';
import { buildDocumentPreview, buildSpreadsheetPreview, decodePreviewText, FilePreviewError, getPreviewKind, loadPreviewBlob, type FilePreviewSource, type SpreadsheetPreview } from '@shared/lib/files/preview';
import { ImageFilePreview } from './ImageFilePreview';
import { PreviewZoomControls } from './PreviewZoomControls';

const PdfFilePreview = lazy(async () => ({ default: (await import('./PdfFilePreview')).PdfFilePreview }));

type Props = { source: FilePreviewSource; onClose: () => void; onDownload?: () => void | Promise<void> };
type Content = { blob: Blob; objectUrl?: string; html?: string; sheets?: SpreadsheetPreview; text?: string; truncated?: boolean };

export const FilePreviewDialog = ({ source, onClose, onDownload }: Props) => {
  const kind = getPreviewKind(source.name);
  const [content, setContent] = useState<Content | null>(null);
  const [busy, setBusy] = useState(kind !== 'unsupported');
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const [sheetIndex, setSheetIndex] = useState(0);
  const [zoom, setZoom] = useState(1);

  // Depend on source primitives: parent list rerenders must not re-download a document.
  const { name, downloadUrl, file } = source;
  useEffect(() => {
    if (kind === 'unsupported') return;
    let active = true;
    let objectUrl: string | undefined;
    const controller = new AbortController();
    setBusy(true); setError(null); setContent(null); setSheetIndex(0); setZoom(1);
    const load = async () => {
      try {
        const blob = await loadPreviewBlob(file ? { name, file } : { name, downloadUrl: downloadUrl! }, controller.signal);
        const next: Content = { blob };
        if (kind === 'docx') next.html = await buildDocumentPreview(blob);
        if (kind === 'xlsx') next.sheets = await buildSpreadsheetPreview(blob);
        if (kind === 'text') {
          next.text = decodePreviewText(await blob.slice(0, 512 * 1024).arrayBuffer());
          next.truncated = blob.size > 512 * 1024;
        }
        if (!active) return;
        if (kind === 'image') { objectUrl = URL.createObjectURL(blob); next.objectUrl = objectUrl; }
        setContent(next);
      } catch (e) { if (active) setError(e instanceof FilePreviewError ? e.message : 'Не удалось открыть файл. Скачайте его для просмотра.'); }
      finally { if (active) setBusy(false); }
    };
    void load();
    return () => { active = false; controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [kind, name, downloadUrl, file, revision]);

  const download = async () => {
    setDownloading(true);
    setDownloadError(null);
    try {
      if (onDownload) await onDownload();
      else if (source.file) {
        const url = URL.createObjectURL(source.file);
        const link = document.createElement('a');
        link.href = url; link.download = source.name; link.click();
        URL.revokeObjectURL(url);
      } else await downloadFile(source.downloadUrl, source.name);
    } catch { setDownloadError('Не удалось скачать файл. Проверьте доступ и повторите попытку.'); }
    finally { setDownloading(false); }
  };
  const sheet = content?.sheets?.[sheetIndex];
  return <Dialog open onClose={onClose} onClick={(event) => event.stopPropagation()} maxWidth="xl" fullWidth aria-labelledby="file-preview-title" PaperProps={{ sx: { m: { xs: 1, sm: 3 }, width: { xs: 'calc(100% - 16px)', sm: 'calc(100% - 48px)' }, height: 'calc(100dvh - 24px)', maxHeight: 'calc(100dvh - 24px)' } }}>
    <DialogTitle id="file-preview-title" component="div" sx={{ flexShrink: 0 }}>
      <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="flex-start">
        <Box sx={{ minWidth: 0 }}><Typography component="h2" variant="h5">Предпросмотр файла</Typography><Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{source.name}</Typography></Box>
        <Stack direction="row" spacing={0.5} flexShrink={0}>
          <Button size="small" startIcon={<DownloadOutlined />} disabled={downloading} onClick={() => void download()}>Скачать</Button>
          <IconButton size="small" aria-label="Закрыть предпросмотр" onClick={onClose}><CloseOutlined /></IconButton>
        </Stack>
      </Stack>
      {kind !== 'unsupported' ? <PreviewZoomControls zoom={zoom} onChange={setZoom} disabled={busy || !content} /> : null}
    </DialogTitle>
    <DialogContent dividers sx={{ p: { xs: 1, sm: 2 }, minHeight: 0, display: 'flex', overflow: 'hidden' }}>
      <Stack spacing={1.5} sx={{ flex: 1, minHeight: 0, minWidth: 0 }}>
        {busy ? <Stack direction="row" spacing={1}><CircularProgress size={20} /><Typography role="status">Загружаем предпросмотр…</Typography></Stack> : null}
        {error ? <Alert severity="error" action={<Button onClick={() => setRevision((value) => value + 1)}>Повторить</Button>}>{error}</Alert> : null}
        {downloadError ? <Alert severity="error" action={<Button disabled={downloading} onClick={() => void download()}>Повторить скачивание</Button>}>{downloadError}</Alert> : null}
        {kind === 'unsupported' ? <Alert severity="info">Предпросмотр этого формата недоступен. Скачайте файл, чтобы открыть его на устройстве.</Alert> : null}
        {content && kind === 'pdf' ? <Suspense fallback={<Typography role="status">Открываем PDF…</Typography>}><PdfFilePreview blob={content.blob} zoom={zoom} /></Suspense> : null}
        {content?.objectUrl ? <ImageFilePreview url={content.objectUrl} name={source.name} zoom={zoom} onError={() => setError('Не удалось отобразить изображение. Скачайте исходный файл.')} /> : null}
        {content?.html !== undefined ? <>
          <Typography variant="body2" color="text.secondary">Упрощённое отображение DOCX. Для исходного оформления скачайте документ.</Typography>
          <Box component="iframe" title={`Документ ${source.name}`} sandbox="" referrerPolicy="no-referrer" srcDoc={content.html.replace('</head>', `<style>body{zoom:${zoom}}</style></head>`)} sx={{ width: '100%', flex: 1, minHeight: 0, border: '1px solid', borderColor: 'divider', bgcolor: '#fff' }} />
        </> : null}
        {content?.sheets ? <>
          <Typography variant="body2" color="text.secondary">Просмотр значений ячеек. Формулы не пересчитываются, исходное оформление доступно в скачанном файле.</Typography>
          {content.sheets.length ? <TextField select size="small" label="Лист" value={sheetIndex} onChange={(event) => setSheetIndex(Number(event.target.value))}>
            {content.sheets.map((item, index) => <MenuItem key={`${index}-${item.name}`} value={index}>{item.name}</MenuItem>)}
          </TextField> : <Typography>В книге нет листов для просмотра.</Typography>}
          {sheet?.truncated ? <Alert severity="info">Показаны первые 500 строк и 50 столбцов. Полные данные доступны при скачивании.</Alert> : null}
          {sheet && sheet.rows.length > 0 ? <TableContainer sx={{ flex: 1, minHeight: 0, border: '1px solid', borderColor: 'divider' }}>
            <Table stickyHeader size="small" aria-label={`Лист ${sheet.name}`} sx={{ zoom }}>
              <TableHead><TableRow><TableCell>№</TableCell>{Array.from({ length: Math.max(...sheet.rows.map((row) => row.length)) }, (_, index) => <TableCell key={index}>{index + 1}</TableCell>)}</TableRow></TableHead>
              <TableBody>{sheet.rows.map((row, rowIndex) => <TableRow key={rowIndex}><TableCell component="th" scope="row">{rowIndex + 1}</TableCell>{row.map((cell, index) => <TableCell key={index} sx={{ minWidth: 110, maxWidth: 450, overflowWrap: 'anywhere' }}>{cell}</TableCell>)}</TableRow>)}</TableBody>
            </Table>
          </TableContainer> : sheet ? <Typography>Лист пуст.</Typography> : null}
        </> : null}
        {content?.text !== undefined ? <>
          {content.truncated ? <Alert severity="info">Показано начало файла. Полный текст доступен при скачивании.</Alert> : null}
          <Box component="pre" sx={{ m: 0, flex: 1, minHeight: 0, overflow: 'auto', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontSize: 14 * zoom }}>{content.text}</Box>
        </> : null}
      </Stack>
    </DialogContent>
  </Dialog>;
};
