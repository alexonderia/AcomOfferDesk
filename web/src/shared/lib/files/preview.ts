import { apiFetch } from '@shared/api/client';

export type FilePreviewSource = { name: string } & (
  { downloadUrl: string; file?: never } | { file: File; downloadUrl?: never }
);
export type PreviewKind = 'pdf' | 'image' | 'docx' | 'xlsx' | 'text' | 'unsupported';
export const MAX_PREVIEW_BYTES = 20 * 1024 * 1024;
export class FilePreviewError extends Error {}

export const getPreviewKind = (name: string): PreviewKind => {
  const extension = name.split('.').pop()?.toLowerCase();
  if (extension === 'pdf' || extension === 'docx' || extension === 'xlsx') return extension;
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'avif'].includes(extension ?? '')) return 'image';
  if (['txt', 'csv', 'log', 'json', 'xml', 'md'].includes(extension ?? '')) return 'text';
  return 'unsupported';
};

export const getPreviewRequestPath = (downloadUrl: string): string => {
  const url = new URL(downloadUrl, window.location.origin);
  if (url.origin !== window.location.origin || !/^\/api\/v1\/files\/\d+\/download\/?$/.test(url.pathname)) {
    throw new FilePreviewError('Некорректная ссылка на файл');
  }
  return url.pathname;
};

export const loadPreviewBlob = async (source: FilePreviewSource, signal: AbortSignal): Promise<Blob> => {
  const tooLarge = () => new FilePreviewError('Для предпросмотра доступны файлы до 20 МБ. Скачайте файл для просмотра.');
  if (source.file) {
    if (source.file.size > MAX_PREVIEW_BYTES) throw tooLarge();
    return source.file;
  }
  const response = await apiFetch(getPreviewRequestPath(source.downloadUrl), { method: 'GET', signal, cache: 'no-store' });
  if (!response.ok) {
    if (response.status === 401 || response.status === 403) throw new FilePreviewError('Нет доступа к просмотру файла. Проверьте права или войдите заново.');
    if (response.status === 404) throw new FilePreviewError('Файл не найден или его содержимое недоступно.');
    throw new FilePreviewError('Не удалось загрузить файл. Повторите попытку.');
  }
  if (Number(response.headers.get('Content-Length')) > MAX_PREVIEW_BYTES) {
    await response.body?.cancel();
    throw tooLarge();
  }
  if (!response.body) throw new FilePreviewError('Файл не содержит данных для просмотра.');
  const reader = response.body.getReader();
  const chunks: Uint8Array<ArrayBuffer>[] = [];
  let size = 0;
  try {
    let chunk = await reader.read();
    while (!chunk.done) {
      const value = chunk.value;
      size += value.byteLength;
      if (size > MAX_PREVIEW_BYTES) {
        await reader.cancel();
        throw tooLarge();
      }
      chunks.push(new Uint8Array(value));
      chunk = await reader.read();
    }
  } finally { reader.releaseLock(); }
  if (!size) throw new FilePreviewError('Файл не содержит данных для просмотра.');
  return new Blob(chunks, { type: response.headers.get('Content-Type') ?? 'application/octet-stream' });
};

// Bound Office ZIP expansion before handing the archive to the document parsers.
export const validateOfficeArchive = (buffer: ArrayBuffer) => {
  const view = new DataView(buffer);
  const invalid = () => new FilePreviewError('Документ повреждён или его формат не поддерживается. Скачайте исходный файл.');
  let end = view.byteLength - 22;
  const minimum = Math.max(0, end - 65535);
  while (end >= minimum && view.getUint32(end, true) !== 0x06054b50) end--;
  if (end < minimum) throw invalid();
  const count = view.getUint16(end + 10, true);
  const centralSize = view.getUint32(end + 12, true);
  let offset = view.getUint32(end + 16, true);
  if (!count || count > 2000 || offset + centralSize > end || view.getUint16(end + 4, true) !== 0) throw invalid();
  let expanded = 0;
  for (let i = 0; i < count; i++) {
    if (offset + 46 > end || view.getUint32(offset, true) !== 0x02014b50) throw invalid();
    if (view.getUint16(offset + 8, true) & 1) throw new FilePreviewError('Документ защищён паролем. Скачайте его для просмотра.');
    expanded += view.getUint32(offset + 24, true);
    if (expanded > 32 * 1024 * 1024) throw new FilePreviewError('Документ слишком большой для предпросмотра. Скачайте исходный файл.');
    offset += 46 + view.getUint16(offset + 28, true) + view.getUint16(offset + 30, true) + view.getUint16(offset + 32, true);
  }
  if (offset > end) throw invalid();
};

export const buildDocumentPreview = async (blob: Blob): Promise<string> => {
  const buffer = await blob.arrayBuffer();
  validateOfficeArchive(buffer);
  const [{ default: mammoth }, { default: createPurifier }] = await Promise.all([import('mammoth/mammoth.browser'), import('dompurify')]);
  const converted = await mammoth.convertToHtml({ arrayBuffer: buffer }, { externalFileAccess: false, includeEmbeddedStyleMap: false });
  const purifier = createPurifier(window);
  purifier.addHook('uponSanitizeAttribute', (_node, attribute) => {
    if (attribute.attrName === 'src' && !/^data:image\/(png|jpeg|gif|webp|bmp);base64,/i.test(attribute.attrValue)) attribute.keepAttr = false;
  });
  const html = purifier.sanitize(converted.value, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ['a', 'form', 'input', 'button', 'video', 'audio', 'iframe', 'style'],
    FORBID_ATTR: ['style', 'srcset', 'href', 'target'],
  });
  return `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font:16px/1.5 Arial,sans-serif;margin:24px;color:#17202a;overflow-wrap:anywhere}table{border-collapse:collapse;max-width:100%;display:block;overflow:auto}td,th{border:1px solid #bbb;padding:6px}img{max-width:100%;height:auto}pre{white-space:pre-wrap}</style></head><body>${html}</body></html>`;
};

export type SpreadsheetPreview = Array<{ name: string; rows: string[][]; truncated: boolean }>;
export const buildSpreadsheetPreview = async (blob: Blob): Promise<SpreadsheetPreview> => {
  const buffer = await blob.arrayBuffer();
  validateOfficeArchive(buffer);
  const { default: readXlsxFile } = await import('read-excel-file/browser');
  const sheets = await readXlsxFile(buffer);
  return sheets.map((sheet) => ({
    name: sheet.sheet,
    rows: sheet.data.slice(0, 500).map((row) => row.slice(0, 50).map((cell) => cell instanceof Date ? cell.toLocaleString('ru-RU') : String(cell ?? ''))),
    truncated: sheet.data.length > 500 || sheet.data.some((row) => row.length > 50),
  }));
};

export const decodePreviewText = (buffer: ArrayBuffer): string => {
  const bytes = new Uint8Array(buffer);
  if (bytes[0] === 0xff && bytes[1] === 0xfe) return new TextDecoder('utf-16le').decode(buffer);
  if (bytes[0] === 0xfe && bytes[1] === 0xff) return new TextDecoder('utf-16be').decode(buffer);
  try { return new TextDecoder('utf-8', { fatal: true }).decode(buffer); }
  catch { return new TextDecoder('windows-1251').decode(buffer); }
};
