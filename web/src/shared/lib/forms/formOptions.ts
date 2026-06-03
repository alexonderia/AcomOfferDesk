import type { UseFormProps } from 'react-hook-form';

/** Enables validation while the user types. */
export const liveFormValidationOptions = {
  mode: 'onChange',
  reValidateMode: 'onChange',
} as const satisfies Pick<UseFormProps<never>, 'mode' | 'reValidateMode'>;
