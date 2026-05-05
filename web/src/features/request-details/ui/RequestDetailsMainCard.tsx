import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import EditOutlined from '@mui/icons-material/EditOutlined';
import {
  Box,
  Button,
  Chip,
  IconButton,
  MenuItem,
  Select,
  Stack,
  Typography
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { MutableRefObject, ReactNode } from 'react';
import type { RequestDetailsFile } from '@shared/api/requests/getRequestDetails';
import { StatusPill, type StatusPillTone } from '@shared/components/StatusPill';
import { formatDate } from '@shared/lib/formatters';
import { RequestDetailsInfoPanel } from '@shared/components/RequestDetailsInfoPanel';
import { useIsMobileViewport } from '@shared/lib/responsive';
import type { RequestStatus } from '../model/requestDetailsUtils';

type RequestStatusOption = {
  value: RequestStatus;
  label: string;
};

const requestStatusPillTone: Record<RequestStatus, StatusPillTone> = {
  open: 'success',
  review: 'warning',
  closed: 'neutral',
  cancelled: 'neutral'
};

type RequestDetailsMainCardProps = {
  requestId: number;
  status: RequestStatus;
  statusOptions: readonly RequestStatusOption[];
  statusColor: string;
  canEditRequest: boolean;
  isEditMode: boolean;
  onStatusChange: (nextStatus: RequestStatus) => void;
  descriptionText: string;
  descriptionTextRef: MutableRefObject<HTMLParagraphElement | null>;
  canExpandDescription: boolean;
  isDescriptionExpanded: boolean;
  onToggleDescription: () => void;
  ownerField: ReactNode;
  existingFiles: RequestDetailsFile[];
  canDeleteRequestFiles: boolean;
  onDownloadFile: (downloadUrl: string, fileName: string) => void;
  onRemoveExistingFile: (fileId: number) => void;
  newFile: File | null;
  onClearNewFile: () => void;
  canUploadRequestFiles: boolean;
  onNewFileSelected: (file: File | null) => void;
  canViewRequestAmounts: boolean;
  deadline: string;
  initialAmount: string;
  finalAmount: string;
  onDeadlineChange: (value: string) => void;
  onInitialAmountChange: (value: string) => void;
  onFinalAmountChange: (value: string) => void;
  requestCreatedAt: string | null;
  requestClosedAt: string | null;
  requestDeadlineAt: string | null;
  requestOfferId: number | string | null;
  showOfferId?: boolean;
  requestUpdatedAt: string | null;
  hideUpdatedAtIfEmpty?: boolean;
  isSaving: boolean;
  canSaveRequestChanges: boolean;
  hasPendingChanges: boolean;
  hasValidationError: boolean;
  canEnterEditMode: boolean;
  onCancelEditing: () => void;
  onSave: () => void;
  onStartEdit: () => void;
  hideActions?: boolean;
};

export const RequestDetailsMainCard = ({
  requestId,
  status,
  statusOptions,
  statusColor,
  canEditRequest,
  isEditMode,
  onStatusChange,
  descriptionText,
  descriptionTextRef,
  canExpandDescription,
  isDescriptionExpanded,
  onToggleDescription,
  ownerField,
  existingFiles,
  canDeleteRequestFiles,
  onDownloadFile,
  onRemoveExistingFile,
  newFile,
  onClearNewFile,
  canUploadRequestFiles,
  onNewFileSelected,
  canViewRequestAmounts,
  deadline,
  initialAmount,
  finalAmount,
  onDeadlineChange,
  onInitialAmountChange,
  onFinalAmountChange,
  requestCreatedAt,
  requestClosedAt,
  requestDeadlineAt,
  requestOfferId,
  showOfferId = true,
  requestUpdatedAt,
  hideUpdatedAtIfEmpty = false,
  isSaving,
  canSaveRequestChanges,
  hasPendingChanges,
  hasValidationError,
  canEnterEditMode,
  onCancelEditing,
  onSave,
  onStartEdit,
  hideActions = false
}: RequestDetailsMainCardProps) => {
  const isMobileViewport = useIsMobileViewport();
  const statusLabel = statusOptions.find((option) => option.value === status)?.label ?? String(status);
  const showStatusSelect = canEditRequest && isEditMode;

  return (
  <Box
    sx={(theme) => ({
      borderRadius: `${theme.acomShape.panelRadius}px`,
      border: `1px solid ${theme.palette.divider}`,
      backgroundColor: theme.palette.background.paper,
      px: { xs: 2, md: 3 },
      py: { xs: 2, md: 2.5 },
      display: 'grid',
      gap: 2.5
    })}
  >
    <Stack
      direction="row"
      alignItems="center"
      justifyContent="space-between"
      spacing={1.5}
      sx={{ flexWrap: 'nowrap' }}
    >
      <Typography variant="h5" fontWeight={700}>
        Заявка №{requestId}
      </Typography>
      {showStatusSelect ? (
        <Select
          size="small"
          value={status}
          onChange={(event) => onStatusChange(event.target.value as RequestStatus)}
          sx={{
            minWidth: 170,
            borderRadius: 999,
            color: statusColor,
            fontWeight: 600,
            backgroundColor: alpha(statusColor, 0.1),
            '& .MuiOutlinedInput-notchedOutline': { borderColor: statusColor },
            '& .MuiSelect-icon': { color: statusColor }
          }}
        >
          {statusOptions.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </Select>
      ) : (
        <Box
          sx={{
            minWidth: 170,
            minHeight: 40,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end'
          }}
        >
          <StatusPill label={statusLabel} tone={requestStatusPillTone[status]} />
        </Box>
      )}
    </Stack>

    <Box
      sx={{
        display: 'grid',
        gap: 2,
        gridTemplateColumns: { xs: '1fr', md: '1.6fr 1fr' },
        alignItems: 'stretch'
      }}
    >
      <Box
        onClick={canExpandDescription ? onToggleDescription : undefined}
        sx={(themeValue) => ({
          border: `1px solid ${themeValue.palette.divider}`,
          borderRadius: `${themeValue.acomShape.controlRadius}px`,
          px: 1.5,
          py: 1,
          minHeight: 74,
          height: '100%',
          cursor: canExpandDescription ? 'pointer' : 'default',
          position: 'relative',
          display: 'grid',
          alignItems: 'center'
        })}
      >
        <Typography
          ref={descriptionTextRef}
          component="p"
          sx={{
            pr: canExpandDescription ? 12 : 0,
            whiteSpace: 'pre-wrap',
            ...(isDescriptionExpanded
              ? {}
              : {
                  display: '-webkit-box',
                  WebkitBoxOrient: 'vertical',
                  WebkitLineClamp: 2,
                  overflow: 'hidden'
                })
          }}
        >
          {descriptionText || 'Описание заявки отсутствует'}
        </Typography>
        {canExpandDescription ? (
          <Typography
            variant="caption"
            sx={{
              position: 'absolute',
              right: 12,
              bottom: 8,
              color: 'primary.main',
              fontWeight: 600
            }}
          >
            {isDescriptionExpanded ? 'Свернуть' : 'Развернуть'}
          </Typography>
        ) : null}
      </Box>
      <Stack spacing={0.6} sx={{ minHeight: 74, height: '100%', justifyContent: 'space-between' }}>
        <Typography variant="body2" color="text.secondary">
          Ответственный по заявке
        </Typography>
        {ownerField}
      </Stack>
    </Box>

    <Stack spacing={0.75}>
      <Typography variant="body2" color="text.secondary">
        Файлы заявки
      </Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap alignItems="center">
        {existingFiles.length > 0 ? (
          existingFiles.map((file) => (
            <Chip
              key={file.id}
              label={file.name}
              variant="outlined"
              onClick={() => onDownloadFile(file.download_url, file.name)}
              onDelete={isEditMode && canDeleteRequestFiles ? () => onRemoveExistingFile(file.id) : undefined}
              sx={{ borderRadius: 999 }}
            />
          ))
        ) : (
          <Typography variant="body2">Файлы не прикреплены</Typography>
        )}
        {newFile ? (
          <Chip
            label={newFile.name}
            variant="outlined"
            color="primary"
            onDelete={onClearNewFile}
            sx={{ borderRadius: 999 }}
          />
        ) : null}
        {isEditMode && canUploadRequestFiles ? (
          <IconButton
            component="label"
            size="small"
            aria-label="Добавить файл"
            sx={{
              alignSelf: 'center',
              color: 'primary.main',
              width: 32,
              height: 32,
              p: 0,
              '&:hover': {
                backgroundColor: 'transparent'
              }
            }}
          >
            <AddCircleOutlineIcon sx={{ fontSize: 32 }} />
            <input
              hidden
              type="file"
              onChange={(event) => {
                onNewFileSelected(event.target.files?.[0] ?? null);
                event.target.value = '';
              }}
            />
          </IconButton>
        ) : null}
      </Stack>
    </Stack>

    <RequestDetailsInfoPanel
      value={{
        createdAt: requestCreatedAt,
        closedAt: requestClosedAt,
        deadlineAt: requestDeadlineAt,
        offerId: String(requestOfferId ?? '-'),
        showOfferId,
        canViewRequestAmounts,
        initialAmountText: initialAmount || '-',
        finalAmountText: finalAmount || '-',
        isEditMode,
        canEditRequest,
        deadlineInputValue: deadline,
        onDeadlineChange,
        initialAmountInputValue: initialAmount,
        finalAmountInputValue: finalAmount,
        onInitialAmountChange,
        onFinalAmountChange
      }}
    />

    <Stack
      direction="row"
      justifyContent="space-between"
      alignItems="center"
      spacing={1}
      sx={{ flexWrap: 'nowrap' }}
    >
      {(!hideUpdatedAtIfEmpty || Boolean(requestUpdatedAt)) ? (
        <Typography variant="body1" sx={{ minHeight: 36, display: 'flex', alignItems: 'center', whiteSpace: 'nowrap' }}>
          Обновлено {formatDate(requestUpdatedAt, true)}
        </Typography>
      ) : (
        <Box sx={{ minHeight: 36 }} />
      )}
      {hideActions ? null : (
        <Stack direction="row" spacing={1} alignItems="center" sx={{ flexWrap: 'nowrap' }}>
          {isEditMode ? (
            <>
              <Button variant="outlined" onClick={onCancelEditing} disabled={isSaving}>
                Отмена
              </Button>
              <Button
                variant={canSaveRequestChanges && hasPendingChanges && !hasValidationError ? 'contained' : 'outlined'}
                onClick={onSave}
                disabled={isSaving || !canSaveRequestChanges || !hasPendingChanges || hasValidationError}
              >
                {isSaving ? 'Сохранение...' : 'Сохранить'}
              </Button>
            </>
          ) : (
            <Button
              variant="outlined"
              startIcon={isMobileViewport ? undefined : <EditOutlined fontSize="small" />}
              onClick={onStartEdit}
              disabled={!canEnterEditMode}
              aria-label="Изменить"
              sx={{
                minHeight: 36,
                minWidth: isMobileViewport ? 40 : undefined,
                width: isMobileViewport ? 40 : 'auto',
                px: isMobileViewport ? 0 : undefined
              }}
            >
              {isMobileViewport ? <EditOutlined fontSize="small" /> : 'Изменить'}
            </Button>
          )}
        </Stack>
      )}
    </Stack>
  </Box>
  );
};
