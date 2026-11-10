import { Blob as NodeBlob } from 'node:buffer';
import { ThemeProvider } from '@mui/material/styles';
import { Chip } from '@mui/material';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiFetch } from '@shared/api/client';
import { downloadFile } from '@shared/api/fileDownload';
import { appTheme } from '@shared/theme/appTheme';
import { FilePreviewDialog } from './FilePreviewDialog';
import { FilePreviewTrigger } from './FilePreviewTrigger';

vi.mock('@shared/api/client', () => ({ apiFetch: vi.fn() }));
vi.mock('@shared/api/fileDownload', () => ({ downloadFile: vi.fn() }));
vi.mock('@shared/lib/files/preview', async (original) => ({
  ...await original<typeof import('@shared/lib/files/preview')>(),
  buildDocumentPreview: vi.fn().mockResolvedValue('<html><body>Document</body></html>'),
  buildSpreadsheetPreview: vi.fn().mockResolvedValue([
    { name: 'First', rows: [['First value']], truncated: false },
    { name: 'Second', rows: [['<script>unsafe()</script>']], truncated: false },
  ]),
}));

const fetchMock = vi.mocked(apiFetch);
const close = vi.fn();
const OriginalURL = URL;
const createObjectURL = vi.fn(() => 'blob:preview-image');
const revokeObjectURL = vi.fn();
const show = (name: string) => render(<ThemeProvider theme={appTheme}><FilePreviewDialog source={{ name, downloadUrl: '/api/v1/files/1/download' }} onClose={close} /></ThemeProvider>);

describe('file preview dialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('Blob', NodeBlob);
    vi.stubGlobal('URL', class extends OriginalURL {
      static createObjectURL = createObjectURL;
      static revokeObjectURL = revokeObjectURL;
    });
    fetchMock.mockResolvedValue(new Response('Safe text <script>not executed</script>', { headers: { 'Content-Type': 'text/plain' } }));
    vi.mocked(downloadFile).mockResolvedValue(undefined);
  });
  afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

  it('keeps unsupported formats downloadable without fetching a preview', async () => {
    show('legacy.doc');
    expect(screen.getByRole('alert')).toHaveTextContent('Предпросмотр этого формата недоступен');
    expect(fetchMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Скачать' }));
    await waitFor(() => expect(downloadFile).toHaveBeenCalledWith('/api/v1/files/1/download', 'legacy.doc'));
  });

  it('renders text as text, never as active HTML', async () => {
    show('text.txt');
    expect(await screen.findByText('Safe text <script>not executed</script>')).toBeInTheDocument();
    expect(document.querySelector('script')).toBeNull();
  });

  it('retries a failed download even when preview is unsupported', async () => {
    vi.mocked(downloadFile).mockRejectedValueOnce(new Error('offline'));
    show('legacy.doc');
    fireEvent.click(screen.getByRole('button', { name: 'Скачать' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Повторить скачивание' }));
    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.queryByText(/Не удалось скачать файл/)).not.toBeInTheDocument());
  });

  it('shows authorization failures and allows retry', async () => {
    fetchMock.mockResolvedValueOnce(new Response('', { status: 403 }));
    show('text.txt');
    expect(await screen.findByRole('alert')).toHaveTextContent('Нет доступа');
    fireEvent.click(screen.getByRole('button', { name: 'Повторить' }));
    expect(await screen.findByText('Safe text <script>not executed</script>')).toBeInTheDocument();
  });

  it('revokes image object URLs when closed', async () => {
    const view = show('image.png');
    await waitFor(() => expect(document.querySelector('img')).not.toBeNull());
    const image = document.querySelector('img')!;
    Object.defineProperty(image, 'naturalWidth', { value: 100 });
    Object.defineProperty(image, 'naturalHeight', { value: 200 });
    fireEvent.load(image);
    expect(await screen.findByRole('img', { name: 'image.png' })).toHaveAttribute('src', 'blob:preview-image');
    view.unmount();
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:preview-image');
  });

  it('fits an image by viewport height and zooms without fetching it again', async () => {
    vi.spyOn(HTMLElement.prototype, 'clientWidth', 'get').mockReturnValue(800);
    vi.spyOn(HTMLElement.prototype, 'clientHeight', 'get').mockReturnValue(600);
    show('portrait.png');
    await waitFor(() => expect(document.querySelector('img')).not.toBeNull());
    const image = document.querySelector('img')!;
    Object.defineProperty(image, 'naturalWidth', { value: 1000 });
    Object.defineProperty(image, 'naturalHeight', { value: 2000 });
    fireEvent.load(image);
    expect(parseFloat(getComputedStyle(image).height)).toBe(584);
    fireEvent.click(screen.getByRole('button', { name: 'Увеличить' }));
    expect(screen.getByText('125%')).toBeInTheDocument();
    expect(parseFloat(getComputedStyle(image).height)).toBe(730);
    fireEvent.click(screen.getByRole('button', { name: 'Уменьшить' }));
    fireEvent.click(screen.getByRole('button', { name: 'Уменьшить' }));
    expect(parseFloat(getComputedStyle(image).height)).toBeCloseTo(438);
    fireEvent.click(screen.getByRole('button', { name: 'По высоте окна' }));
    expect(parseFloat(getComputedStyle(image).height)).toBe(584);
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it('aborts a pending request when unmounted', async () => {
    fetchMock.mockImplementation(() => new Promise(() => {}));
    const view = show('text.txt');
    await waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    const signal = fetchMock.mock.calls[0][1]?.signal;
    view.unmount();
    expect(signal?.aborted).toBe(true);
  });

  it('isolates converted Word HTML in a sandboxed iframe', async () => {
    show('document.docx');
    const frame = await screen.findByTitle('Документ document.docx');
    expect(frame).toHaveAttribute('sandbox', '');
    expect(frame).toHaveAttribute('referrerpolicy', 'no-referrer');
    expect(frame).toHaveAttribute('srcdoc', '<html><body>Document</body></html>');
  });

  it('switches spreadsheet sheets and treats cell markup as text', async () => {
    show('table.xlsx');
    expect(await screen.findByText('First value')).toBeInTheDocument();
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Лист' }));
    fireEvent.click(await screen.findByRole('option', { name: 'Second' }));
    expect(await screen.findByText('<script>unsafe()</script>')).toBeInTheDocument();
    expect(document.querySelector('script')).toBeNull();
  });

  it('does not navigate the parent row when opening or operating the preview', async () => {
    const rowClick = vi.fn();
    render(<ThemeProvider theme={appTheme}><div onClick={rowClick}>
      <FilePreviewTrigger source={{ name: 'legacy.doc', downloadUrl: '/api/v1/files/1/download' }}>
        {(open) => <Chip label="Attachment" onClick={open} />}
      </FilePreviewTrigger>
    </div></ThemeProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'Attachment' }));
    await screen.findByRole('button', { name: 'Закрыть предпросмотр' });
    await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Скачать' })));
    fireEvent.click(screen.getByRole('button', { name: 'Закрыть предпросмотр' }));
    expect(rowClick).not.toHaveBeenCalled();
  });
});
