export const MAX_UPLOAD_FILE_SIZE_BYTES = 5 * 1024 * 1024;
export const MAX_UPLOAD_FILE_SIZE_MB = 5;
export const ALLOWED_UPLOAD_FILE_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.jpg', '.jpeg', '.png'] as const;
export const ALLOWED_UPLOAD_FILE_INPUT_ACCEPT = ALLOWED_UPLOAD_FILE_EXTENSIONS.join(',');
export const ALLOWED_UPLOAD_FILE_TYPES_LABEL = ALLOWED_UPLOAD_FILE_EXTENSIONS.join(', ');

export const getUploadFileSizeError = (file: File): string | null => {
  if (file.size > MAX_UPLOAD_FILE_SIZE_BYTES) {
    return `Файл слишком большой. Размер одного файла не должен превышать ${MAX_UPLOAD_FILE_SIZE_MB} МБ.`;
  }
  return null;
};

export const getFileKey = (file: File) => `${file.name}-${file.size}-${file.lastModified}`;

export const mergeUniqueFiles = (currentFiles: File[], addedFiles: File[]) => {
  const fileMap = new Map<string, File>();
  [...currentFiles, ...addedFiles].forEach((file) => fileMap.set(getFileKey(file), file));
  return Array.from(fileMap.values());
};
