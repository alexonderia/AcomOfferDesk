import { ThemeProvider } from '@mui/material/styles';
import type { MutableRefObject } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { RequestDetailsMainCard } from './RequestDetailsMainCard';
import { appTheme } from '@shared/theme/appTheme';

vi.mock('@shared/lib/responsive', () => ({
  useIsMobileViewport: () => false
}));

const statusOptions = [
  { value: 'open', label: 'Open' },
  { value: 'review', label: 'Review' },
  { value: 'closed', label: 'Closed' },
  { value: 'cancelled', label: 'Cancelled' }
] as const;

const renderCard = (responsibleContact?: { fullName?: string | null; phone?: string | null; mail?: string | null }) =>
  render(
    <ThemeProvider theme={appTheme}>
      <RequestDetailsMainCard
        requestId="17"
        status="open"
        statusOptions={statusOptions}
        statusColor="#2e7d32"
        canEditRequest={false}
        isEditMode={false}
        onStatusChange={() => undefined}
        descriptionText="Request description"
        descriptionTextRef={{ current: null } as MutableRefObject<HTMLParagraphElement | null>}
        canExpandDescription={false}
        isDescriptionExpanded={false}
        onToggleDescription={() => undefined}
        ownerField={<div>Owner field</div>}
        responsibleContact={responsibleContact}
        existingFiles={[]}
        canDeleteRequestFiles={false}
        onDownloadFile={() => undefined}
        onRemoveExistingFile={() => undefined}
        newFiles={[]}
        onRemoveNewFile={() => undefined}
        canUploadRequestFiles={false}
        onNewFilesAdded={() => undefined}
        canViewRequestAmounts={false}
        deadline=""
        initialAmount=""
        finalAmount=""
        onDeadlineChange={() => undefined}
        onInitialAmountChange={() => undefined}
        onFinalAmountChange={() => undefined}
        requestCreatedAt="2026-05-19T00:00:00Z"
        requestClosedAt={null}
        requestDeadlineAt="2026-05-20T00:00:00Z"
        requestOfferId={null}
        requestUpdatedAt="2026-05-20T00:00:00Z"
        isSaving={false}
        canSaveRequestChanges={false}
        hasPendingChanges={false}
        hasValidationError={false}
        canEnterEditMode={false}
        onCancelEditing={() => undefined}
        onSave={() => undefined}
        onStartEdit={() => undefined}
        hideActions
      />
    </ThemeProvider>
  );

describe('RequestDetailsMainCard', () => {
  it('renders responsible contact block when contact data is provided', () => {
    renderCard({
      fullName: 'Alice Example',
      phone: '+7 900 123-45-67',
      mail: 'alice@example.com'
    });

    expect(screen.queryByText('Контакты ответственного')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Показать контакты ответственного')).toBeInTheDocument();
    expect(screen.getByText('Alice Example')).toBeInTheDocument();
    expect(screen.getByText('+7 900 123-45-67')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();

    const contactPanel = screen.getByText('Alice Example').closest('[data-highlighted]');
    expect(contactPanel).toHaveAttribute('data-highlighted', 'false');

    const infoButton = screen.getByLabelText('Показать контакты ответственного');
    fireEvent.mouseEnter(infoButton);
    expect(screen.getByText('Alice Example').closest('[data-highlighted]')).toHaveAttribute(
      'data-highlighted',
      'true'
    );

    fireEvent.mouseLeave(infoButton);
    expect(screen.getByText('Alice Example').closest('[data-highlighted]')).toHaveAttribute(
      'data-highlighted',
      'false'
    );
  });

  it('keeps the contact block hidden when no contact data is provided', () => {
    renderCard();

    expect(screen.queryByLabelText('Показать контакты ответственного')).not.toBeInTheDocument();
    expect(screen.queryByText('ФИО')).not.toBeInTheDocument();
  });
});
