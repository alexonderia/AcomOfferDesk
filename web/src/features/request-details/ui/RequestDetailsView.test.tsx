import { forwardRef, type ReactNode } from "react";
import { ThemeProvider } from "@mui/material/styles";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RequestDetailsView } from "@features/request-details/ui/RequestDetailsView";
import { getRequestDetails } from "@shared/api/requests/getRequestDetails";
import { appTheme } from "@shared/theme/appTheme";

vi.mock("@features/request-details/model/useRequestDetails", () => ({
  useRequestDetails: () => ({
    navigate: vi.fn(),
    requestId: 17,
  }),
}));

vi.mock("@shared/api/requests/getRequestDetails", () => ({
  getRequestDetails: vi.fn(),
}));

vi.mock("@shared/api/requests/getRequestEconomists", () => ({
  getRequestEconomists: vi.fn().mockResolvedValue([]),
}));

vi.mock("@shared/api/plans", () => ({
  getPlanOptions: vi.fn().mockResolvedValue([]),
}));

vi.mock("@shared/api/requests/updateRequestDetails", () => ({
  updateRequestDetails: vi.fn(),
  uploadRequestFile: vi.fn(),
  deleteRequestFile: vi.fn(),
}));

vi.mock("@shared/api/requests/sendRequestEmailNotifications", () => ({
  sendRequestEmailNotifications: vi.fn(),
}));

vi.mock("@shared/api/offers/markDeletedAlertViewed", () => ({
  markDeletedAlertViewed: vi.fn(),
}));

vi.mock("@shared/api/offers/updateOfferStatus", () => ({
  updateOfferStatus: vi.fn(),
}));

vi.mock("@shared/api/fileDownload", () => ({
  downloadFile: vi.fn(),
}));

vi.mock("@features/request-details/ui/RequestDetailsMainCard", () => ({
  RequestDetailsMainCard: (props: {
    canEditRequest: boolean;
    canUpdateRequestStatus?: boolean;
    canDeleteRequestFiles: boolean;
    canUploadRequestFiles: boolean;
    canEnterEditMode: boolean;
  }) => (
    <div data-testid="request-details-main-card">
      <div data-testid="main-can-edit-request">{String(props.canEditRequest)}</div>
      <div data-testid="main-can-update-request-status">{String(Boolean(props.canUpdateRequestStatus))}</div>
      <div data-testid="main-can-delete-request-files">{String(props.canDeleteRequestFiles)}</div>
      <div data-testid="main-can-upload-request-files">{String(props.canUploadRequestFiles)}</div>
      <div data-testid="main-can-enter-edit-mode">{String(props.canEnterEditMode)}</div>
    </div>
  ),
}));

vi.mock("@features/request-details/ui/OffersTable", () => ({
  OffersTable: (props: { canChangeStatus?: boolean; onAddClick?: (() => void) | undefined }) => (
    <div data-testid="offers-table">
      <div data-testid="offers-can-change-status">{String(Boolean(props.canChangeStatus))}</div>
      <div data-testid="offers-has-add-click">{String(Boolean(props.onAddClick))}</div>
    </div>
  ),
}));

vi.mock("@features/request-details/ui/CreateManualOfferDialog", () => ({
  CreateManualOfferDialog: () => <div data-testid="create-manual-offer-dialog" />,
}));

vi.mock("@shared/components/AdditionalEmailsField", () => ({
  AdditionalEmailsField: forwardRef(() => <div data-testid="additional-emails-field" />),
}));

vi.mock("@shared/components/ToggleSection", () => ({
  ToggleSection: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

const buildRequestDetails = (overrides?:
  Partial<{
    requestActions: {
      edit: boolean;
      update_status: boolean;
      change_owner: boolean;
      upload_file: boolean;
      delete_file: boolean;
      send_email_notifications: boolean;
      mark_deleted_alert_viewed: boolean;
      create_offer: boolean;
      view_amounts: boolean;
    };
    offerActions: { accept: boolean; reject: boolean };
  }>) => ({
  id: 17,
  id_user: "owner-1",
  owner_full_name: "Owner One",
  status: "open",
  status_label: "Open",
  initial_amount: 100,
  final_amount: 90,
  deadline_at: "2026-05-20T00:00:00Z",
  closed_at: null,
  id_offer: null,
  id_plan: null,
  description: "Request details",
  created_at: "2026-05-19T00:00:00Z",
  updated_at: "2026-05-20T00:00:00Z",
  count_submitted: 0,
  count_deleted_alert: 0,
  count_accepted_total: 0,
  count_rejected_total: 0,
  files: [],
  offers: [
    {
      offer_id: 101,
      status: "submitted",
      offer_amount: 95,
      created_at: "2026-05-19T00:00:00Z",
      updated_at: "2026-05-20T00:00:00Z",
      files: [],
      actions: {
        open_workspace: true,
        view_contractor_info: true,
        edit_amount: true,
        accept: overrides?.offerActions?.accept ?? true,
        reject: overrides?.offerActions?.reject ?? true,
        delete: false,
        upload_file: false,
        delete_file: false,
      },
    },
  ],
  actions: {
    view_details: true,
    view_amounts: overrides?.requestActions?.view_amounts ?? true,
    open_contractor_view: false,
    edit: overrides?.requestActions?.edit ?? true,
    update_status: overrides?.requestActions?.update_status ?? true,
    change_owner: overrides?.requestActions?.change_owner ?? true,
    upload_file: overrides?.requestActions?.upload_file ?? true,
    delete_file: overrides?.requestActions?.delete_file ?? true,
    send_email_notifications: overrides?.requestActions?.send_email_notifications ?? true,
    mark_deleted_alert_viewed: overrides?.requestActions?.mark_deleted_alert_viewed ?? true,
    create_offer: overrides?.requestActions?.create_offer ?? true,
  },
});

const renderWithTheme = () =>
  render(
    <ThemeProvider theme={appTheme}>
      <RequestDetailsView />
    </ThemeProvider>
  );

describe("RequestDetailsView action-driven CTAs", () => {
  beforeEach(() => {
    vi.mocked(getRequestDetails).mockReset();
  });

  it("enables critical request/offers controls when backend actions are true", async () => {
    vi.mocked(getRequestDetails).mockResolvedValue(buildRequestDetails() as never);

    renderWithTheme();

    await waitFor(() => {
      expect(screen.getByTestId("request-details-main-card")).toBeInTheDocument();
    });

    expect(screen.getByTestId("main-can-edit-request")).toHaveTextContent("true");
    expect(screen.getByTestId("main-can-update-request-status")).toHaveTextContent("true");
    expect(screen.getByTestId("main-can-delete-request-files")).toHaveTextContent("true");
    expect(screen.getByTestId("main-can-upload-request-files")).toHaveTextContent("true");
    expect(screen.getByTestId("main-can-enter-edit-mode")).toHaveTextContent("true");
    expect(screen.getByTestId("offers-can-change-status")).toHaveTextContent("true");
    expect(screen.getByTestId("offers-has-add-click")).toHaveTextContent("true");

    const sendEmailButton = screen.getByRole("button", { name: "Отправить" });
    expect(sendEmailButton).toBeEnabled();
  });

  it("disables or removes critical controls when backend actions are false", async () => {
    vi.mocked(getRequestDetails).mockResolvedValue(
      buildRequestDetails({
        requestActions: {
          edit: false,
          update_status: false,
          change_owner: false,
          upload_file: false,
          delete_file: false,
          send_email_notifications: false,
          mark_deleted_alert_viewed: false,
          create_offer: false,
          view_amounts: false,
        },
        offerActions: {
          accept: false,
          reject: false,
        },
      }) as never
    );

    renderWithTheme();

    await waitFor(() => {
      expect(screen.getByTestId("request-details-main-card")).toBeInTheDocument();
    });

    expect(screen.getByTestId("main-can-edit-request")).toHaveTextContent("false");
    expect(screen.getByTestId("main-can-update-request-status")).toHaveTextContent("false");
    expect(screen.getByTestId("main-can-delete-request-files")).toHaveTextContent("false");
    expect(screen.getByTestId("main-can-upload-request-files")).toHaveTextContent("false");
    expect(screen.getByTestId("main-can-enter-edit-mode")).toHaveTextContent("false");
    expect(screen.getByTestId("offers-can-change-status")).toHaveTextContent("false");
    expect(screen.getByTestId("offers-has-add-click")).toHaveTextContent("false");

    const sendEmailButton = screen.getByRole("button", { name: "Отправить" });
    expect(sendEmailButton).toBeDisabled();
  });

  it("enables edit entry point when backend allows owner change even if direct edit is disabled", async () => {
    vi.mocked(getRequestDetails).mockResolvedValue(
      buildRequestDetails({
        requestActions: {
          edit: false,
          update_status: false,
          change_owner: true,
          upload_file: false,
          delete_file: false,
          send_email_notifications: false,
          mark_deleted_alert_viewed: false,
          create_offer: false,
          view_amounts: false,
        },
        offerActions: {
          accept: false,
          reject: false,
        },
      }) as never
    );

    renderWithTheme();

    await waitFor(() => {
      expect(screen.getByTestId("request-details-main-card")).toBeInTheDocument();
    });

    expect(screen.getByTestId("main-can-edit-request")).toHaveTextContent("false");
    expect(screen.getByTestId("main-can-enter-edit-mode")).toHaveTextContent("true");
  });
});

