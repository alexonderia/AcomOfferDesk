import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ConfirmationDialog } from './ConfirmationDialog';

describe('ConfirmationDialog', () => {
  it('focuses cancellation and cancels by button, Escape or backdrop without confirming', () => {
    const onCancel = vi.fn();
    const onConfirm = vi.fn();
    render(<ConfirmationDialog open title="Удаление" description="Удалить объект?"
      confirmLabel="Удалить" onCancel={onCancel} onConfirm={onConfirm} />);
    expect(screen.getByRole('dialog', { name: 'Удаление' })).toHaveAccessibleDescription('Удалить объект?');
    expect(screen.getByRole('button', { name: 'Отмена' })).toHaveFocus();
    fireEvent.click(screen.getByRole('button', { name: 'Отмена' }));
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape', keyCode: 27 });
    fireEvent.mouseDown(document.querySelector('.MuiDialog-container')!);
    fireEvent.click(document.querySelector('.MuiDialog-container')!);
    expect(onCancel).toHaveBeenCalledTimes(3);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('prevents duplicate confirmation and dismissal while an action is running', async () => {
    let finish!: () => void;
    const onConfirm = vi.fn(() => new Promise<void>(resolve => { finish = resolve; }));
    const onCancel = vi.fn();
    const props = { open: true, title: 'Удаление', confirmLabel: 'Удалить', pendingLabel: 'Удаляем...', onConfirm, onCancel };
    const { rerender } = render(<ConfirmationDialog {...props} />);
    fireEvent.click(screen.getByRole('button', { name: 'Удалить' }));
    fireEvent.click(screen.getByRole('button', { name: 'Удалить' }));
    expect(onConfirm).toHaveBeenCalledOnce();
    rerender(<ConfirmationDialog {...props} isPending />);
    expect(screen.getByRole('button', { name: 'Отмена' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Удаляем...' })).toBeDisabled();
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape', keyCode: 27 });
    fireEvent.mouseDown(document.querySelector('.MuiDialog-container')!);
    fireEvent.click(document.querySelector('.MuiDialog-container')!);
    expect(onCancel).not.toHaveBeenCalled();
    await act(async () => finish());
    rerender(<ConfirmationDialog {...props} />);
    expect(screen.getByRole('button', { name: 'Отмена' })).toBeEnabled();
    fireEvent.click(screen.getByRole('button', { name: 'Отмена' }));
    expect(onCancel).toHaveBeenCalledOnce();
  });
});
