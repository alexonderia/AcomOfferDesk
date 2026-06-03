import { useForm, type FieldValues, type UseFormProps } from 'react-hook-form';
import { liveFormValidationOptions } from './formOptions';

export const useLiveValidatedForm = <
  TFieldValues extends FieldValues = FieldValues,
  TContext = unknown,
>(
  props?: UseFormProps<TFieldValues, TContext>
) =>
  useForm<TFieldValues, TContext>({
    ...liveFormValidationOptions,
    ...props,
  });
