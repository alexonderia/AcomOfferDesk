import { TextField, type TextFieldProps } from '@mui/material';
import type { UseFormRegisterReturn } from 'react-hook-form';
import { textFieldAutocompleteProps } from '@shared/lib/forms';
import { PasswordTextField } from './PasswordTextField';

type ValidatedTextFieldProps = TextFieldProps & {
  fieldName?: string;
  registration?: UseFormRegisterReturn;
};

export const ValidatedTextField = ({
  fieldName,
  registration,
  inputProps,
  ...props
}: ValidatedTextFieldProps) => {
  const autocompleteInputProps = fieldName ? textFieldAutocompleteProps(fieldName).inputProps : undefined;
  const { ref: registrationRef, ...registrationProps } = registration ?? {};
  const fieldProps = {
    ...registrationProps,
    inputRef: registrationRef,
    inputProps: { ...autocompleteInputProps, ...inputProps },
    ...props,
  };
  return props.type === 'password' ? <PasswordTextField {...fieldProps} /> : <TextField {...fieldProps} />;
};
