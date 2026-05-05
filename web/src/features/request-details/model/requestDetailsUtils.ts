import type { RequestDetails } from '@shared/api/requests/getRequestDetails';

export type RequestStatus = 'open' | 'review' | 'closed' | 'cancelled';

export const statusOptions = [
    { value: 'open', label: 'Открыта', color: '#2e7d32' },
    { value: 'review', label: 'На рассмотрении', color: '#ed6c02' },
    { value: 'closed', label: 'Закрыта', color: '#787878ff' },
    { value: 'cancelled', label: 'Отменена', color: '#d32f2f' }
] as const;

export const detailsColumns = [
    { key: 'label', label: 'Параметр' },
    { key: 'value', label: 'Значение' }
];

export const toDateInputValue = (value: string | null) => {
    if (!value) return '';
    const [datePart] = value.split('T');
    return datePart ?? '';
};

export const toAmountInputValue = (value: number | null | undefined) => {
    if (value === null || value === undefined || Number.isNaN(value)) {
        return '';
    }
    return String(value);
};

export const parseAmountInput = (value: string) => {
    const normalized = value.trim().replace(',', '.');
    if (!normalized) {
        return null;
    }
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : Number.NaN;
};

export const normalizeOfferStatus = (value: string | null): 'accepted' | 'rejected' | '' => {
    if (value === 'accepted' || value === 'rejected') {
        return value;
    }
    return '';
};

export const buildRequestDetailsSignature = (request: RequestDetails | null) => {
    if (!request) {
        return '';
    }

    return JSON.stringify({
        id: request.id,
        id_user: request.id_user,
        status: request.status,
        deadline_at: request.deadline_at,
        updated_at: request.updated_at,
        initial_amount: request.initial_amount,
        final_amount: request.final_amount,
        id_offer: request.id_offer,
        id_plan: request.id_plan,
        count_deleted_alert: request.count_deleted_alert,
        offers: request.offers.map((offer) => ({
            id: offer.offer_id,
            status: offer.status,
            updated_at: offer.updated_at,
            amount: offer.offer_amount,
            unread_messages_count: offer.unread_messages_count ?? 0,
            files: offer.files.map((file) => [file.id, file.name])
        })),
        files: request.files.map((file) => [file.id, file.name])
    });
};

export const toDeadlineIso = (date: string) => `${date}T23:59:59`;
