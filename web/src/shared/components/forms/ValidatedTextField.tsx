import { TextField, type TextFieldProps } from '@mui/material';
import type { UseFormRegisterReturn } from 'react-hook-form';
import { textFieldAutocompleteProps } from '@shared/lib/forms';

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

  return (
    <TextField
      {...registration}
      inputProps={{
        ...autocompleteInputProps,
        ...inputProps,
      }}
      {...props}
    />
  );
};
