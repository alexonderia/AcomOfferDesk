export type AutocompleteToken =
  | 'given-name'
  | 'family-name'
  | 'name'
  | 'email'
  | 'tel'
  | 'username'
  | 'current-password'
  | 'new-password'
  | 'organization'
  | 'street-address'
  | 'off';

const AUTOCOMPLETE_BY_FIELD: Record<string, AutocompleteToken> = {
  login: 'username',
  username: 'username',
  oldPassword: 'current-password',
  password: 'new-password',
  password_confirm: 'new-password',
  confirmPassword: 'new-password',
  firstName: 'given-name',
  lastName: 'family-name',
  full_name: 'name',
  fullName: 'name',
  phone: 'tel',
  company_phone: 'tel',
  companyPhone: 'tel',
  mail: 'email',
  company_mail: 'email',
  companyMail: 'email',
  company_name: 'organization',
  companyName: 'organization',
  address: 'street-address',
  inn: 'off',
  note: 'off',
  text: 'off',
  requestNumber: 'off',
  initialAmount: 'off',
  description: 'off',
  offerAmount: 'off',
  role_id: 'off',
  id_parent: 'off',
  status: 'off',
  started_at: 'off',
  ended_at: 'off',
  user_status: 'off',
};

export const resolveAutocompleteToken = (fieldName: string): AutocompleteToken =>
  AUTOCOMPLETE_BY_FIELD[fieldName] ?? 'off';

export const textFieldAutocompleteProps = (fieldName: string) => ({
  inputProps: {
    autoComplete: resolveAutocompleteToken(fieldName),
  },
});
