import { readFileSync } from 'node:fs';
import { Blob as NodeBlob } from 'node:buffer';
import { resolve } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiFetch } from '@shared/api/client';
import { buildDocumentPreview, buildSpreadsheetPreview, decodePreviewText, getPreviewKind, getPreviewRequestPath, loadPreviewBlob, MAX_PREVIEW_BYTES, validateOfficeArchive } from './preview';

vi.mock('@shared/api/client', () => ({ apiFetch: vi.fn() }));
// Vitest/jsdom uses a separate ArrayBuffer realm. Exercise the same real DOCX
// converter through its Node input adapter; browser-bundle loading is checked in E2E.
vi.mock('mammoth/mammoth.browser', async () => {
  const mammoth = await import('mammoth');
  const { Buffer } = await import('node:buffer');
  return { default: { convertToHtml: ({ arrayBuffer }: { arrayBuffer: ArrayBuffer }, options: object) => mammoth.convertToHtml({ buffer: Buffer.from(arrayBuffer) }, options) } };
});
const fetchMock = vi.mocked(apiFetch);
const fixture = (name: string) => readFileSync(resolve(__dirname, '__fixtures__', name));
const buffer = (name: string) => new Uint8Array(fixture(name)).buffer;

describe('authorized file previews', () => {
  beforeEach(() => { vi.stubGlobal('Blob', NodeBlob); fetchMock.mockReset(); });
  afterEach(() => vi.unstubAllGlobals());

  it.each([['a.PDF', 'pdf'], ['a.png', 'image'], ['a.jpeg', 'image'], ['a.docx', 'docx'], ['a.xlsx', 'xlsx'], ['a.txt', 'text'], ['a.html', 'unsupported'], ['a.svg', 'unsupported'], ['a.doc', 'unsupported']])('classifies %s as %s', (name, expected) => {
    expect(getPreviewKind(name)).toBe(expected);
  });

  it('uses only authorized same-origin file URLs', () => {
    expect(getPreviewRequestPath('/api/v1/files/12/download')).toBe('/api/v1/files/12/download');
    expect(() => getPreviewRequestPath('https://external.example/api/v1/files/12/download')).toThrow('Некорректная ссылка');
    expect(() => getPreviewRequestPath('/api/v1/users')).toThrow();
  });

  it('fetches through auth runtime and passes cancellation', async () => {
    fetchMock.mockResolvedValue(new Response('preview', { headers: { 'Content-Type': 'text/plain' } }));
    const signal = new AbortController().signal;
    const result = await loadPreviewBlob({ name: 'file.txt', downloadUrl: '/api/v1/files/12/download' }, signal);
    expect(await result.text()).toBe('preview');
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/files/12/download', { method: 'GET', signal, cache: 'no-store' });
  });

  it.each([401, 403, 404, 503])('handles HTTP %s without exposing response bodies', async (status) => {
    fetchMock.mockResolvedValue(new Response('internal-sensitive-error', { status }));
    await expect(loadPreviewBlob({ name: 'file.pdf', downloadUrl: '/api/v1/files/12/download' }, new AbortController().signal)).rejects.not.toThrow('internal-sensitive-error');
  });

  it('rejects oversized responses before consuming their body', async () => {
    fetchMock.mockResolvedValue(new Response('preview', { headers: { 'Content-Length': String(MAX_PREVIEW_BYTES + 1) } }));
    await expect(loadPreviewBlob({ name: 'file.pdf', downloadUrl: '/api/v1/files/12/download' }, new AbortController().signal)).rejects.toThrow('20 МБ');
  });

  it('previews local files without uploading them', async () => {
    const file = new File(['draft'], 'draft.txt');
    expect(await loadPreviewBlob({ name: file.name, file }, new AbortController().signal)).toBe(file);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('stops a response exceeding the limit even without a Content-Length header', async () => {
    const stream = new ReadableStream({ start(controller) {
      controller.enqueue(new Uint8Array(MAX_PREVIEW_BYTES + 1));
      controller.close();
    } });
    fetchMock.mockResolvedValue(new Response(stream));
    await expect(loadPreviewBlob({ name: 'file.pdf', downloadUrl: '/api/v1/files/12/download' }, new AbortController().signal)).rejects.toThrow('20 МБ');
  });

  it('converts a real DOCX with a table and removes executable links', async () => {
    const html = await buildDocumentPreview(new Blob([fixture('preview.docx')]));
    expect(html).toContain('Preview document');
    expect(html).toContain('<table>');
    expect(html).toContain('Table cell');
    expect(html).not.toContain('javascript:');
    expect(html).not.toContain('<a ');
    expect(html).toContain("default-src 'none'");
    expect(html).toContain("font-src data:");
    expect(html).toContain('font:16px/1.5 "Alabuga Sans",sans-serif');
    expect(html).toContain('@font-face');
  });

  it('reads real XLSX sheets and cached formula values without evaluating code', async () => {
    const sheets = await buildSpreadsheetPreview(new Blob([fixture('preview.xlsx')]));
    expect(sheets.map((sheet) => sheet.name)).toEqual(['First sheet', 'Second sheet']);
    expect(sheets[0].rows[0]).toEqual(['First sheet value', '21']);
    expect(sheets[0].rows[1][1]).toBe('42');
    expect(sheets[1].rows[0][0]).toBe('<script>alert(1)</script>');
  });

  it('rejects corrupt and over-expanded Office archives before parsing', () => {
    expect(() => validateOfficeArchive(new ArrayBuffer(3))).toThrow('повреждён');
    const data = buffer('preview.docx');
    const view = new DataView(data);
    let end = data.byteLength - 22;
    while (view.getUint32(end, true) !== 0x06054b50) end--;
    const central = view.getUint32(end + 16, true);
    view.setUint32(central + 24, 33 * 1024 * 1024, true);
    expect(() => validateOfficeArchive(data)).toThrow('слишком большой');
  });

  it('decodes Cyrillic UTF-8 and Windows-1251 text', () => {
    expect(decodePreviewText(new TextEncoder().encode('Привет').buffer)).toBe('Привет');
    expect(decodePreviewText(new Uint8Array([0xcf, 0xf0, 0xe8, 0xe2, 0xe5, 0xf2]).buffer)).toBe('Привет');
  });
});
