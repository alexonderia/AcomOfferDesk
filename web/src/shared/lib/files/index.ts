export const MAX_UPLOAD_FILE_SIZE_BYTES = 5 * 1024 * 1024;
export const MAX_UPLOAD_FILE_SIZE_MB = 5;

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
