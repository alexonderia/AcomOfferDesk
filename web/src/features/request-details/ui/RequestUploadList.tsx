import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined';
import { Box, Button, Checkbox, FormControlLabel, IconButton, List, ListItem, Stack, Typography } from '@mui/material';
import { FilePreviewTrigger } from '@shared/components/file-preview/FilePreviewTrigger';
import { getFileKey } from '@shared/lib/files';

export const RequestUploadList = ({ files, hiddenKeys, extractionKeys, onHiddenChange, onExtractionChange, onRemove, disabled = false }: {
  files: File[];
  hiddenKeys: string[];
  extractionKeys: string[];
  onHiddenChange: (file: File, checked: boolean) => void;
  onExtractionChange: (file: File, checked: boolean) => void;
  onRemove: (file: File) => void;
  disabled?: boolean;
}) => <List aria-label="Файлы заявки" disablePadding sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
  {files.map((file, index) => <ListItem key={getFileKey(file)} divider={index < files.length - 1}
    sx={{ display: 'block', px: 1.5, py: 1 }}>
    <Stack direction="row" alignItems="center" spacing={1}>
      <InsertDriveFileOutlinedIcon color="action" fontSize="small" />
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <FilePreviewTrigger source={{ name: file.name, file }}>
          {(open) => <Button onClick={open} size="small" sx={{ px: 0, justifyContent: 'flex-start', textAlign: 'left', textTransform: 'none', overflowWrap: 'anywhere', maxWidth: '100%', minWidth: 0 }}>
            {file.name}
          </Button>}
        </FilePreviewTrigger>
        <Typography variant="caption" color="text.secondary" display="block">{file.size < 1024 * 1024
          ? `${Math.ceil(file.size / 1024)} КБ`
          : `${(file.size / 1024 / 1024).toLocaleString('ru-RU', { maximumFractionDigits: 2 })} МБ`}</Typography>
      </Box>
      <IconButton size="small" aria-label={`Удалить файл: ${file.name}`} disabled={disabled} onClick={() => onRemove(file)}>
        <DeleteOutlineIcon fontSize="small" />
      </IconButton>
    </Stack>
    <Stack direction="row" useFlexGap flexWrap="wrap" columnGap={1.5}>
      <FormControlLabel sx={{ m: 0, '& .MuiFormControlLabel-label': { fontSize: 13 } }} label="Скрыть от контрагентов"
        control={<Checkbox size="small" checked={hiddenKeys.includes(getFileKey(file))} disabled={disabled}
          inputProps={{ 'aria-label': `Скрыть от контрагентов: ${file.name}` }}
          onChange={(_event, checked) => onHiddenChange(file, checked)} />} />
      <FormControlLabel sx={{ m: 0, '& .MuiFormControlLabel-label': { fontSize: 13 } }} label="Выделить спецификацию"
        control={<Checkbox size="small" checked={extractionKeys.includes(getFileKey(file))} disabled={disabled}
          inputProps={{ 'aria-label': `Выделить спецификацию: ${file.name}` }}
          onChange={(_event, checked) => onExtractionChange(file, checked)} />} />
    </Stack>
  </ListItem>)}
</List>;
