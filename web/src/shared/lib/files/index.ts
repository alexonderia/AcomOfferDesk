export const getFileKey = (file: File) => `${file.name}-${file.size}-${file.lastModified}`;

export const mergeUniqueFiles = (currentFiles: File[], addedFiles: File[]) => {
  const fileMap = new Map<string, File>();
  [...currentFiles, ...addedFiles].forEach((file) => fileMap.set(getFileKey(file), file));
  return Array.from(fileMap.values());
};
