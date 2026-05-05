import { Button, Dialog, DialogContent, Stack, Typography } from '@mui/material';
import { alpha, type Theme } from '@mui/material/styles';
import type { FormEventHandler, ReactNode } from 'react';
import { blurActiveElement } from '@shared/lib/dom/blurActiveElement';
import {
  UnavailabilityStatusSection,
  type UnavailabilityPeriodView
} from './UnavailabilityStatusSection';

type UnavailabilityManagementSectionProps = {
  currentPeriod: UnavailabilityPeriodView | null;
  periods: UnavailabilityPeriodView[];
  canEdit?: boolean;
  isDialogOpen?: boolean;
  onOpenDialog?: () => void;
  onCloseDialog?: () => void;
  onSubmit?: FormEventHandler<HTMLFormElement>;
  isSubmitting?: boolean;
  editor?: ReactNode;
  dialogNotice?: ReactNode;
  triggerLabel?: string;
  dialogTitle?: string;
  submitLabel?: string;
};

const dialogPaperSx = (theme: Theme) => ({
  borderRadius: 2,
  px: { xs: 2.5, sm: 3.5 },
  py: { xs: 3, sm: 3.5 },
  backgroundColor: theme.palette.background.default,
  maxHeight: 'min(760px, calc(100vh - 32px))',
  overflow: 'hidden',
  boxShadow: `0 24px 80px ${alpha(theme.palette.common.black, 0.18)}`
});

const dialogContentSx = {
  p: 0,
  overflowX: 'hidden',
  overflowY: 'auto',
  scrollbarWidth: 'none',
  '&::-webkit-scrollbar': {
    display: 'none'
  }
};

export const UnavailabilityManagementSection = ({
  currentPeriod,
  periods,
  canEdit = false,
  isDialogOpen = false,
  onOpenDialog,
  onCloseDialog,
  onSubmit,
  isSubmitting = false,
  editor,
  dialogNotice,
  triggerLabel = 'Установить нерабочий период',
  dialogTitle = 'Установить нерабочий период',
  submitLabel = 'Сохранить'
}: UnavailabilityManagementSectionProps) => {
  const handleOpenDialog = () => {
    blurActiveElement();
    onOpenDialog?.();
  };

  return (
    <Stack spacing={1.5}>
      <UnavailabilityStatusSection currentPeriod={currentPeriod} periods={periods} />

      {canEdit ? (
        <>
          <Button variant="outlined" sx={{ borderRadius: 1, textTransform: 'none' }} onClick={handleOpenDialog}>
            {triggerLabel}
          </Button>

          <Dialog
            open={isDialogOpen}
            onClose={onCloseDialog}
            fullWidth
            maxWidth="sm"
            PaperProps={{
              sx: dialogPaperSx
            }}
          >
            <DialogContent sx={dialogContentSx}>
              <Stack spacing={2} component="form" onSubmit={onSubmit}>
                <Typography variant="h5" fontWeight={600} lineHeight={1}>
                  {dialogTitle}
                </Typography>
                {dialogNotice}
                {editor}
                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  sx={{ borderRadius: 1, textTransform: 'none', py: 1.25, fontSize: 16, fontWeight: 700, boxShadow: 'none' }}
                  disabled={isSubmitting}
                >
                  {submitLabel}
                </Button>
              </Stack>
            </DialogContent>
          </Dialog>
        </>
      ) : null}
    </Stack>
  );
};
