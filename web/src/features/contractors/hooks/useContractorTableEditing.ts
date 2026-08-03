import { useCallback, useEffect, useMemo, useState } from 'react';
import type { UserListItem } from '@entities/user';
import { normalizeUserStatus } from '@features/admin/components/UserCardPrimitives';
import type { ContractorListItem } from '@shared/api/contractors/listContractors';
import { updateContractorStatus } from '@shared/api/contractors/updateContractorStatus';
import { updateManualContractor } from '@shared/api/users/updateManualContractor';
import {
  buildManualContractorDraft,
  buildManualContractorPayload,
  normalizeOptionalContractorValue,
  type ManualContractorDraft,
  type ManualContractorEditableField,
  validateContractorEditRow,
} from '@shared/lib/manualContractorEditing';
import { formatRuPhone } from '@shared/lib/phone';
import { useSystemToasts } from '@shared/ui/toasts';
import { formatPhoneForView } from '../components/contractorUi';

export type ContractorEditStatus = 'review' | 'active' | 'inactive' | 'blacklist';
export type ContractorEditDraft = Partial<ManualContractorDraft & { status: ContractorEditStatus }>;
export type ContractorEditField = keyof ContractorEditDraft;
export type ContractorFieldErrors = Partial<Record<ContractorEditField, string>>;

const MANUAL_EDITABLE_FIELDS: ManualContractorEditableField[] = [
  'full_name',
  'phone',
  'mail',
  'company_name',
  'inn',
  'company_phone',
  'company_mail',
  'address',
  'note',
];

const toUserListItem = (row: ContractorListItem): UserListItem => ({
  user_id: row.userId,
  role_id: row.roleId,
  id_parent: null,
  status: row.status,
  full_name: row.fullName,
  phone: row.phone,
  mail: row.mail,
  company_name: row.companyName,
  inn: row.inn,
  company_phone: row.companyPhone,
  company_mail: row.companyMail,
  address: row.address,
  note: row.note,
  units_count: 0,
  managers_count: 0,
  subordinates_count: 0,
  actions: row.actions,
});

const toManualDraft = (row: ContractorListItem, draft: ContractorEditDraft): ManualContractorDraft => ({
  ...buildManualContractorDraft(toUserListItem(row)),
  ...Object.fromEntries(
    MANUAL_EDITABLE_FIELDS
      .filter((field) => typeof draft[field] === 'string')
      .map((field) => [field, draft[field] as string])
  ),
});

export const getContractorFieldValue = (row: ContractorListItem, field: ContractorEditField): string => {
  switch (field) {
    case 'login':
      return row.userId;
    case 'full_name':
      return normalizeOptionalContractorValue(row.fullName);
    case 'phone':
      return formatPhoneForView(row.phone) ?? '';
    case 'mail':
      return normalizeOptionalContractorValue(row.mail);
    case 'company_name':
      return normalizeOptionalContractorValue(row.companyName);
    case 'inn':
      return normalizeOptionalContractorValue(row.inn);
    case 'company_phone':
      return formatPhoneForView(row.companyPhone) ?? '';
    case 'company_mail':
      return normalizeOptionalContractorValue(row.companyMail);
    case 'address':
      return normalizeOptionalContractorValue(row.address);
    case 'note':
      return normalizeOptionalContractorValue(row.note);
    case 'status':
      return normalizeUserStatus(row.status);
    default:
      return '';
  }
};

const areContractorFieldValuesEqual = (
  row: ContractorListItem,
  field: ContractorEditField,
  nextValue: string,
) => {
  if (field === 'phone' || field === 'company_phone') {
    const currentValue = formatRuPhone(getContractorFieldValue(row, field)) || getContractorFieldValue(row, field);
    const normalizedNextValue = formatRuPhone(nextValue) || nextValue;
    return normalizeOptionalContractorValue(currentValue) === normalizeOptionalContractorValue(normalizedNextValue);
  }
  return normalizeOptionalContractorValue(getContractorFieldValue(row, field))
    === normalizeOptionalContractorValue(nextValue);
};

export const isContractorFieldDirty = (
  row: ContractorListItem,
  field: ContractorEditField,
  draft: ContractorEditDraft,
) => draft[field] !== undefined && !areContractorFieldValuesEqual(row, field, String(draft[field]));

type UseContractorTableEditingOptions = {
  rows: ContractorListItem[];
  isEditMode: boolean;
  onSaved: () => Promise<void>;
};

export const useContractorTableEditing = ({
  rows,
  isEditMode,
  onSaved,
}: UseContractorTableEditingOptions) => {
  const { showSystemToast } = useSystemToasts();
  const [draftsById, setDraftsById] = useState<Record<string, ContractorEditDraft>>({});
  const [fieldErrorsById, setFieldErrorsById] = useState<Record<string, ContractorFieldErrors>>({});
  const [rowErrorsById, setRowErrorsById] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!isEditMode) {
      setDraftsById({});
      setFieldErrorsById({});
      setRowErrorsById({});
    }
  }, [isEditMode]);

  const dirtyRowCount = useMemo(
    () => Object.values(draftsById).filter((draft) => Object.keys(draft).length > 0).length,
    [draftsById],
  );

  const hasUnsavedEdits = dirtyRowCount > 0;

  const updateDraftValue = useCallback((row: ContractorListItem, field: ContractorEditField, value: string) => {
    const normalizedValue = field === 'phone' || field === 'company_phone'
      ? formatRuPhone(value) || value
      : value;

    setRowErrorsById((prev) => {
      if (!prev[row.userId]) {
        return prev;
      }
      const next = { ...prev };
      delete next[row.userId];
      return next;
    });

    let nextDraftForValidation: ContractorEditDraft = {};

    setDraftsById((prev) => {
      const currentDraft = prev[row.userId] ?? {};
      const nextDraft = {
        ...currentDraft,
        [field]: normalizedValue,
      };
      if (!isContractorFieldDirty(row, field, nextDraft)) {
        delete nextDraft[field];
      }
      nextDraftForValidation = nextDraft;
      const next = { ...prev };
      if (Object.keys(nextDraft).length === 0) {
        delete next[row.userId];
      } else {
        next[row.userId] = nextDraft;
      }
      return next;
    });

    if (!row.actions.manage_manual_contractor) {
      return;
    }

    const manualDraft = toManualDraft(row, nextDraftForValidation);
    const rowFieldErrors = validateContractorEditRow(toUserListItem(row), manualDraft);

    setFieldErrorsById((prev) => {
      const next = { ...prev };
      if (Object.keys(rowFieldErrors).length === 0) {
        delete next[row.userId];
      } else {
        next[row.userId] = rowFieldErrors;
      }
      return next;
    });
  }, []);

  const handleCancel = useCallback(() => {
    setDraftsById({});
    setFieldErrorsById({});
    setRowErrorsById({});
  }, []);

  const handleSave = useCallback(async () => {
    const validationErrors: Record<string, ContractorFieldErrors> = {};

    for (const [rowId, draft] of Object.entries(draftsById)) {
      const row = rows.find((item) => item.userId === rowId);
      if (!row) {
        continue;
      }
      if (row.actions.manage_manual_contractor) {
        const manualDraft = toManualDraft(row, draft);
        const fieldErrors = validateContractorEditRow(toUserListItem(row), manualDraft);
        if (Object.keys(fieldErrors).length > 0) {
          validationErrors[rowId] = fieldErrors;
        }
      }
    }

    if (Object.keys(validationErrors).length > 0) {
      setFieldErrorsById(validationErrors);
      const messages = Object.entries(validationErrors).flatMap(([rowId, errors]) =>
        Object.values(errors).map((message) => `${rowId}: ${message}`),
      );
      messages.forEach((message) => {
        showSystemToast({
          severity: 'warning',
          message,
        });
      });
      return;
    }

    setIsSaving(true);
    setFieldErrorsById({});
    setRowErrorsById({});

    try {
      const entries = Object.entries(draftsById);
      const results = await Promise.allSettled(
        entries.map(async ([rowId, draft]) => {
          const row = rows.find((item) => item.userId === rowId);
          if (!row) {
            return rowId;
          }

          if (row.actions.manage_manual_contractor) {
            const manualDraft = toManualDraft(row, draft);
            const { payload } = buildManualContractorPayload(toUserListItem(row), manualDraft);
            if (Object.keys(payload).length > 0) {
              await updateManualContractor(row.userId, payload);
            }
          }

          if (draft.status !== undefined && row.actions.update_status) {
            await updateContractorStatus(row.userId, { user_status: draft.status });
          }

          return rowId;
        }),
      );

      const successIds = new Set<string>();
      const nextRowErrors: Record<string, string> = {};

      results.forEach((result, index) => {
        const rowId = entries[index]?.[0];
        if (!rowId) {
          return;
        }
        if (result.status === 'fulfilled') {
          successIds.add(rowId);
          return;
        }
        nextRowErrors[rowId] = result.reason instanceof Error
          ? result.reason.message
          : 'Не удалось сохранить изменения в строке';
      });

      setDraftsById((prev) => {
        const next = { ...prev };
        successIds.forEach((rowId) => {
          delete next[rowId];
        });
        return next;
      });
      setFieldErrorsById((prev) => {
        const next = { ...prev };
        successIds.forEach((rowId) => {
          delete next[rowId];
        });
        return next;
      });
      setRowErrorsById(nextRowErrors);

      if (successIds.size > 0) {
        await onSaved();
      }

      Object.entries(nextRowErrors).forEach(([rowId, message]) => {
        showSystemToast({
          severity: 'error',
          message: `${rowId}: ${message}`,
        });
      });

      if (successIds.size > 0 && Object.keys(nextRowErrors).length === 0) {
        showSystemToast({
          severity: 'success',
          message: 'Изменения сохранены.',
        });
      } else if (successIds.size > 0) {
        showSystemToast({
          severity: 'warning',
          message: 'Часть строк сохранена, часть требует внимания.',
        });
      } else if (Object.keys(nextRowErrors).length === 0) {
        showSystemToast({
          severity: 'error',
          message: 'Не удалось сохранить изменения.',
        });
      }
    } finally {
      setIsSaving(false);
    }
  }, [draftsById, onSaved, rows, showSystemToast]);

  const getDraft = useCallback(
    (row: ContractorListItem) => draftsById[row.userId] ?? {},
    [draftsById],
  );

  const getFieldError = useCallback(
    (row: ContractorListItem, field: ContractorEditField) => fieldErrorsById[row.userId]?.[field],
    [fieldErrorsById],
  );

  const rowHasEdits = useCallback(
    (row: ContractorListItem) => Object.keys(draftsById[row.userId] ?? {}).length > 0,
    [draftsById],
  );

  return {
    draftsById,
    fieldErrorsById,
    rowErrorsById,
    dirtyRowCount,
    hasUnsavedEdits,
    isSaving,
    updateDraftValue,
    handleCancel,
    handleSave,
    getDraft,
    getFieldError,
    rowHasEdits,
    isFieldDirty: isContractorFieldDirty,
    getFieldValue: getContractorFieldValue,
  };
};

