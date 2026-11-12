import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen } from '@testing-library/react';
import { useForm } from 'react-hook-form';
import { describe, expect, it, vi } from 'vitest';
import { appTheme } from '@shared/theme/appTheme';
import { PlanDialogs } from './PlanDialogs';
import type { RootPlanFormValues, SubplanFormValues, DelegateFormValues, EditFormValues } from './planDashboardForms';

const Harness = () => {
  const rootPlanForm = useForm<RootPlanFormValues>({ defaultValues: { name: '', periodStart: '', periodEnd: '', planAmount: '' } });
  const subplanForm = useForm<SubplanFormValues>();
  const delegateForm = useForm<DelegateFormValues>();
  const editForm = useForm<EditFormValues>();
  const noop = vi.fn();
  return <ThemeProvider theme={appTheme}><PlanDialogs
    isMutating={false} canCreateRootPlan rootDialogOpen
    subplanNode={null} delegateNode={null} delegateCandidates={[]} isCandidatesLoading={false}
    editNode={null} deleteNode={null} closeNode={null}
    rootPlanForm={rootPlanForm} subplanForm={subplanForm} delegateForm={delegateForm} editForm={editForm}
    onCloseRootDialog={noop} onCloseSubplanDialog={noop} onCloseDelegateDialog={noop}
    onCloseEditDialog={noop} onCloseDeleteDialog={noop} onCloseCloseDialog={noop}
    onSubmitRoot={noop} onSubmitSubplan={noop} onSubmitDelegate={noop} onSubmitEdit={noop}
    onConfirmDelete={noop} onConfirmClose={noop}
  /></ThemeProvider>;
};

const marker = (label: string) => screen.getByLabelText(label).closest('.MuiFormControl-root')?.querySelector('label [title]');

describe('plan creation required fields', () => {
  it('reflects field validity and cross-field dates before submission', () => {
    render(<Harness />);
    for (const label of ['Название плана', 'Дата начала', 'Дата окончания', 'Сумма плана']) {
      expect(screen.getByLabelText(label)).toBeRequired();
      expect(marker(label)).toHaveAttribute('title', 'Обязательное поле');
    }
    fireEvent.change(screen.getByLabelText('Название плана'), { target: { value: 'План' } });
    fireEvent.change(screen.getByLabelText('Дата начала'), { target: { value: '2026-11-15' } });
    fireEvent.change(screen.getByLabelText('Дата окончания'), { target: { value: '2026-11-14' } });
    fireEvent.change(screen.getByLabelText('Сумма плана'), { target: { value: '-1' } });
    expect(marker('Название плана')).toHaveAttribute('title', 'Поле заполнено верно');
    expect(marker('Дата окончания')).toHaveAttribute('title', 'Обязательное поле');
    expect(marker('Сумма плана')).toHaveAttribute('title', 'Обязательное поле');
    fireEvent.change(screen.getByLabelText('Дата окончания'), { target: { value: '2026-11-16' } });
    fireEvent.change(screen.getByLabelText('Сумма плана'), { target: { value: '0' } });
    expect(marker('Дата окончания')).toHaveAttribute('title', 'Поле заполнено верно');
    expect(marker('Сумма плана')).toHaveAttribute('title', 'Поле заполнено верно');
    fireEvent.change(screen.getByLabelText('Дата начала'), { target: { value: '2026-11-17' } });
    expect(marker('Дата окончания')).toHaveAttribute('title', 'Обязательное поле');
  });
});
