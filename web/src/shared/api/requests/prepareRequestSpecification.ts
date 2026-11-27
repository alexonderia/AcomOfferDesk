import { fetchJson } from '../client';

export type PreparedRequestSpecification = {
  file: File;
  confirmation: string;
  itemCount: number;
  usedOcr: boolean;
};

type SpecificationResponse = {
  name: string;
  mime_type: string;
  content_base64: string;
  confirmation: string;
  item_count: number;
  used_ocr: boolean;
};

export const prepareRequestSpecification = async (requestId: string, files: File[], extractionIndices: number[], publicSourceIndices: number[], signal: AbortSignal): Promise<PreparedRequestSpecification> => {
  const body = new FormData();
  body.append('request_id', requestId.trim());
  files.forEach((file) => body.append('files', file, file.name));
  extractionIndices.forEach((index) => body.append('extraction_indices', String(index)));
  publicSourceIndices.forEach((index) => body.append('public_source_indices', String(index)));
  const result = await fetchJson<SpecificationResponse>('/api/v1/requests/specification-preview',
    { method: 'POST', body, signal }, 'Не удалось выделить спецификацию');
  const bytes = Uint8Array.from(atob(result.content_base64), (char) => char.charCodeAt(0));
  return {
    file: new File([bytes], result.name, { type: result.mime_type }),
    confirmation: result.confirmation,
    itemCount: result.item_count,
    usedOcr: result.used_ocr,
  };
};
