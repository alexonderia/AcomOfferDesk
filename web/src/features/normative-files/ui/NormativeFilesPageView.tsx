import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  MenuItem,
  Select,
  Stack,
} from '@mui/material';
import { useRef, useState } from 'react';
import { useAuth } from '@app/providers/AuthProvider';
import { uploadNormativeFile } from '@shared/api/normative';
import { normativeFileStatusLabels, type NormativeFileItem, type NormativeFileStatus } from '@shared/api/normative/types';
import { hasPermission } from '@shared/auth/permissions';
import { DataTable, type DataTableColumn } from '@shared/components/DataTable';
import { downloadFile } from '@shared/api/fileDownload';
import { getUploadFileSizeError } from '@shared/lib/files';
import { useSystemToasts } from '@shared/ui/toasts';
import { useNormativeFilesPage } from '../model/useNormativeFilesPage';

const columns: DataTableColumn[] = [
  { key: 'name', label: 'Имя файла', minWidth: 280, fraction: 2.5 },
  { key: 'status', label: 'Статус', minWidth: 180, fraction: 1 },
  { key: 'actions', label: 'Действия', minWidth: 220, fraction: 1.2 },
];

const statusOptions: NormativeFileStatus[] = ['actual', 'outdated'];

export const NormativeFilesPageView = () => {
  const { session } = useAuth();
  const canUpdateNormativeFileStatus = hasPermission(session, 'normative_files.status.update');
  const canCreateNormativeFile = hasPermission(session, 'normative_files.create');
  const { items, isLoading, error, updatingIds, reload, handleStatusChange } = useNormativeFilesPage();
  const { showErrorToast, showSuccessToast } = useSystemToasts();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleDownload = async (item: NormativeFileItem) => {
    try {
      await downloadFile(item.download_url, item.original_name);
    } catch (downloadError) {
      showErrorToast(downloadError instanceof Error ? downloadError.message : 'Не удалось скачать файл');
    }
  };

  const handleStatusUpdate = async (item: NormativeFileItem, nextStatus: NormativeFileStatus) => {
    try {
      await handleStatusChange(item, nextStatus);
      showSuccessToast('Статус нормативного документа обновлен');
    } catch (updateError) {
      showErrorToast(
        updateError instanceof Error ? updateError.message : 'Не удалось обновить статус нормативного документа'
      );
    }
  };

  const handleUpload = async (file: File) => {
    const sizeError = getUploadFileSizeError(file);
    if (sizeError) {
      showErrorToast(sizeError);
      return;
    }

    setIsUploading(true);
    try {
      await uploadNormativeFile(file);
      showSuccessToast('Нормативный документ загружен');
      await reload();
    } catch (uploadError) {
      showErrorToast(uploadError instanceof Error ? uploadError.message : 'Не удалось загрузить нормативный документ');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <Stack spacing={1.5}>
      {canCreateNormativeFile ? (
        <input
          ref={fileInputRef}
          type="file"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) {
              void handleUpload(file);
            }
          }}
        />
      ) : null}

      {error ? <Alert severity="error">{error}</Alert> : null}

      <Box sx={{ minWidth: 0 }}>
        <DataTable<NormativeFileItem>
          columns={columns}
          rows={items}
          rowKey={(row) => row.id}
          renderRow={(row) => [
            row.original_name,
            canUpdateNormativeFileStatus ? (
              <Stack key={`status-${row.id}`} direction="row" spacing={1} alignItems="center">
                <FormControl size="small" sx={{ minWidth: 160 }}>
                  <Select
                    value={row.status}
                    disabled={updatingIds.has(row.id)}
                    onChange={(event) => {
                      void handleStatusUpdate(row, event.target.value as NormativeFileStatus);
                    }}
                    sx={{ borderRadius: 1, backgroundColor: 'background.paper' }}
                  >
                    {statusOptions.map((status) => (
                      <MenuItem key={status} value={status}>
                        {normativeFileStatusLabels[status]}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                {updatingIds.has(row.id) ? <CircularProgress size={18} /> : null}
              </Stack>
            ) : (
              normativeFileStatusLabels[row.status]
            ),
            <Button
              key={`actions-${row.id}`}
              variant="outlined"
              size="small"
              startIcon={<DownloadOutlinedIcon />}
              onClick={() => void handleDownload(row)}
              sx={{ textTransform: 'none', borderRadius: 1 }}
            >
              Скачать
            </Button>,
          ]}
          isLoading={isLoading}
          emptyMessage="Нормативные документы не добавлены"
          storageKey="normative-files"
          stickyLastColumn={false}
          addButtonLabel={isUploading ? 'Загружаем...' : 'Добавить документ'}
          onAddClick={
            canCreateNormativeFile
              ? () => {
                  if (!isUploading) {
                    fileInputRef.current?.click();
                  }
                }
              : undefined
          }
          showAddAction={canCreateNormativeFile}
        />
      </Box>
    </Stack>
  );
};
