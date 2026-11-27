import { useId, useRef, type ReactNode } from 'react';
import { Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, type DialogProps } from '@mui/material';

export type ConfirmationDialogProps = {
  open: boolean;
  title: string;
  description?: ReactNode;
  children?: ReactNode;
  confirmLabel: string;
  pendingLabel?: string;
  color?: 'primary' | 'error' | 'warning';
  maxWidth?: DialogProps['maxWidth'];
  isPending?: boolean;
  confirmDisabled?: boolean;
  onCancel: () => void;
  onConfirm: () => void | Promise<void>;
};

export const ConfirmationDialog = ({
  open, title, description, children, confirmLabel, pendingLabel = 'Выполняем...',
  color = 'primary', maxWidth = 'sm', isPending = false, confirmDisabled = false, onCancel, onConfirm,
}: ConfirmationDialogProps) => {
  const id = useId();
  const isConfirmingRef = useRef(false);
  const handleCancel = () => {
    if (!isPending && !isConfirmingRef.current) onCancel();
  };
  const handleConfirm = async () => {
    if (isPending || confirmDisabled || isConfirmingRef.current) return;
    isConfirmingRef.current = true;
    try {
      await onConfirm();
    } finally {
      isConfirmingRef.current = false;
    }
  };

  return (
    <Dialog open={open} onClose={handleCancel} fullWidth maxWidth={maxWidth}
      aria-labelledby={`${id}-title`} aria-describedby={`${id}-content`}>
      <DialogTitle id={`${id}-title`}>{title}</DialogTitle>
      <DialogContent id={`${id}-content`} dividers aria-busy={isPending} sx={{ overflowWrap: 'anywhere' }}>
        {description ? <DialogContentText>{description}</DialogContentText> : null}
        {children}
      </DialogContent>
      <DialogActions sx={{ flexWrap: 'wrap', gap: 1 }}>
        <Button autoFocus disabled={isPending} onClick={handleCancel}>Отмена</Button>
        <Button variant="contained" color={color} disabled={isPending || confirmDisabled} onClick={() => void handleConfirm()}>
          {isPending ? pendingLabel : confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
