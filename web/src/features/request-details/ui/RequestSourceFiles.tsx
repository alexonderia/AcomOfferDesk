import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { Alert, Box, Button, Chip, ClickAwayListener, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import { useRef, useState } from 'react';
import { FilePreviewTrigger } from '@shared/components/file-preview/FilePreviewTrigger';
import { ALLOWED_UPLOAD_FILE_INPUT_ACCEPT, MAX_UPLOAD_FILE_SIZE_MB, getFileKey } from '@shared/lib/files';
import { useRequestSourceFiles } from '../model/useRequestSourceFiles';

export const RequestSourceFiles = ({ requestId, canUpload = false, canDelete = false, isEditMode = false, isSaving = false,
  newFiles = [], deletedFileIds = [], onFilesAdded, onRemoveFile, onRemoveNewFile, refreshRevision = 0 }: {
  requestId: string; canUpload?: boolean; canDelete?: boolean; isEditMode?: boolean; isSaving?: boolean;
  newFiles?: File[]; deletedFileIds?: number[]; refreshRevision?: number;
  onFilesAdded?: (files: File[]) => void; onRemoveFile?: (id: number) => void; onRemoveNewFile?: (file: File) => void;
}) => {
  const { files, loading, error, retry } = useRequestSourceFiles(requestId, refreshRevision);
  const inputRef = useRef<HTMLInputElement>(null);
  const [infoOpen, setInfoOpen] = useState(false);
  const showUpload = isEditMode && canUpload;
  if (!showUpload && !loading && !error && !files.length && !newFiles.length) return null;
  return <Stack spacing={0.75}>
    <Stack direction="row" spacing={0.5} alignItems="center">
      <Typography variant="body2" color="text.secondary">Скрытые файлы заявки</Typography>
      <ClickAwayListener onClickAway={() => setInfoOpen(false)}>
        <Box component="span" sx={{ display: 'inline-flex' }}>
          <Tooltip open={infoOpen} onOpen={() => setInfoOpen(true)} onClose={() => setInfoOpen(false)}
            arrow describeChild placement="top" disableTouchListener disableHoverListener disableFocusListener
            componentsProps={{ tooltip: { sx: { maxWidth: 'min(360px, calc(100vw - 32px))', overflowWrap: 'anywhere', p: 1.25 } } }}
            title={<Stack spacing={1}>
              <Typography variant="body2">Доступны сотрудникам с доступом к заявке. Контрагенты их не видят.</Typography>
              {canUpload ? <Typography variant="body2">Добавленные здесь файлы сохраняются как закрытые приложения и не меняют сформированную заявку. Каждый файл — до {MAX_UPLOAD_FILE_SIZE_MB} МБ.</Typography> : null}
              <Typography variant="body2">Добавление и удаление доступны при редактировании. Изменения применяются кнопкой «Сохранить». Исходники ТЗ и файлы с неизвестным назначением удалить нельзя.</Typography>
            </Stack>}>
            <IconButton size="small" color="primary" aria-label="О скрытых файлах заявки" onClick={() => setInfoOpen(true)}
              onMouseEnter={() => setInfoOpen(true)} onFocus={() => setInfoOpen(true)} onBlur={() => setInfoOpen(false)}
              sx={{ p: 0.25 }}>
              <InfoOutlinedIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
        </Box>
      </ClickAwayListener>
    </Stack>
    {loading ? <Typography role="status">Загружаем скрытые файлы…</Typography> : null}
    {error ? <Alert severity="error" action={<Button onClick={retry}>Повторить</Button>}>{error}</Alert> : null}
    <Stack direction="row" useFlexGap flexWrap="wrap" spacing={1} alignItems="center">
      {files.filter((file) => !deletedFileIds.includes(file.id)).map((file) => <FilePreviewTrigger key={file.id} source={{ name: file.name, downloadUrl: file.download_url }}>
        {(open) => <Tooltip arrow describeChild placement="top" title={file.is_specification_source === true
          ? 'Исходник для ТЗ' : file.is_specification_source === false ? 'Скрытое вложение' : 'Назначение неизвестно'}>
          <Chip label={file.name} variant="outlined" onClick={open}
            onDelete={isEditMode && !isSaving && canDelete && file.can_delete === true && file.is_specification_source === false
              ? () => onRemoveFile?.(file.id) : undefined}
            sx={{ borderRadius: 999, maxWidth: '100%' }} />
        </Tooltip>}
      </FilePreviewTrigger>)}
      {newFiles.map((file) => <FilePreviewTrigger key={getFileKey(file)} source={{ name: file.name, file }}>
        {(open) => <Chip label={file.name} variant="outlined" color="primary" onClick={open}
          onDelete={isEditMode && !isSaving ? () => onRemoveNewFile?.(file) : undefined}
          sx={{ borderRadius: 999, maxWidth: '100%' }} />}
      </FilePreviewTrigger>)}
      {showUpload && !error ? <>
        <input ref={inputRef} type="file" hidden multiple accept={ALLOWED_UPLOAD_FILE_INPUT_ACCEPT} disabled={isSaving || loading}
          onChange={(event) => {
            const addedFiles = Array.from(event.target.files ?? []);
            event.target.value = '';
            if (addedFiles.length) onFilesAdded?.(addedFiles);
          }} />
        <IconButton size="small" aria-label="Добавить скрытый файл" disabled={isSaving || loading}
          onClick={() => inputRef.current?.click()} sx={{ color: 'primary.main', width: 32, height: 32, p: 0, '&:hover': { backgroundColor: 'transparent' } }}>
          <AddCircleOutlineIcon sx={{ fontSize: 32 }} />
        </IconButton>
      </> : null}
    </Stack>
  </Stack>;
};
