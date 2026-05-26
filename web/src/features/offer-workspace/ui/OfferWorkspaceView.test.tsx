import type { ReactNode } from "react";
import { ThemeProvider } from "@mui/material/styles";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OfferWorkspaceView } from "@features/offer-workspace/ui/OfferWorkspaceView";
import { appTheme } from "@shared/theme/appTheme";

const useOfferWorkspaceMock = vi.fn();

vi.mock("@features/offer-workspace/model/useOfferWorkspace", () => ({
  useOfferWorkspace: () => useOfferWorkspaceMock(),
}));

vi.mock("@shared/api/fileDownload", () => ({
  downloadFile: vi.fn(),
}));

vi.mock("@features/request-details/ui/RequestDetailsMainCard", () => ({
  RequestDetailsMainCard: () => <div data-testid="workspace-request-card" />,
}));

vi.mock("@features/offer-workspace/ui/OfferWorkspaceChatDock", () => ({
  OFFER_WORKSPACE_CHAT_WIDTH_PX: 430,
  OfferWorkspaceChatDock: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@features/offer-workspace/ui/OfferWorkspaceChatPanel", () => ({
  OfferWorkspaceChatPanel: (props: {
    canSendMessage: boolean;
    canSendMessageWithAttachments: boolean;
  }) => (
    <div data-testid="workspace-chat-panel">
      <div data-testid="chat-can-send-message">{String(props.canSendMessage)}</div>
      <div data-testid="chat-can-attach">{String(props.canSendMessageWithAttachments)}</div>
    </div>
  ),
}));

const buildWorkspaceHookState = (overrides?:
  Partial<{
    isContractor: boolean;
    canUpload: boolean;
    canDeleteFile: boolean;
    canSendMessage: boolean;
    canViewMessages: boolean;
    canSendMessageWithAttachments: boolean;
    canEditOfferStatus: boolean;
    canEditOfferAmount: boolean;
    canDeleteOwnOffer: boolean;
    createOffer: boolean;
    offerAccept: boolean;
    offerReject: boolean;
    offerEditAmount: boolean;
    offerUploadFile: boolean;
    offerDeleteFile: boolean;
    offerDelete: boolean;
  }>) => {
  const selectedOffer = {
    offer_id: 101,
    contractor_user_id: "contractor-1",
    status: "submitted",
    status_label: "Submitted",
    offer_amount: 120,
    created_at: "2026-05-20T00:00:00Z",
    updated_at: "2026-05-20T00:00:00Z",
    files: [
      {
        id: 1,
        path: "offers/1/spec.pdf",
        name: "spec.pdf",
        download_url: "/api/v1/files/1",
      },
    ],
    actions: {
      open_workspace: true,
      view_contractor_info: true,
      edit_amount: overrides?.offerEditAmount ?? true,
      accept: overrides?.offerAccept ?? false,
      reject: overrides?.offerReject ?? false,
      delete: overrides?.offerDelete ?? true,
      upload_file: overrides?.offerUploadFile ?? true,
      delete_file: overrides?.offerDeleteFile ?? true,
    },
  };

  return {
    session: { login: "u-1" },
    workspace: {
      request: {
        request_id: 17,
        description: "Workspace request",
        status: "open",
        status_label: "Open",
        owner_full_name: "Owner One",
        initial_amount: 150,
        final_amount: 120,
        deadline_at: "2026-05-31T00:00:00Z",
        created_at: "2026-05-20T00:00:00Z",
        updated_at: "2026-05-20T00:00:00Z",
        closed_at: null,
        files: [],
        actions: {
          view_details: true,
          view_amounts: true,
          open_contractor_view: false,
          edit: false,
          change_owner: false,
          upload_file: false,
          delete_file: false,
          send_email_notifications: false,
          mark_deleted_alert_viewed: false,
          create_offer: overrides?.createOffer ?? true,
        },
      },
      offer: selectedOffer,
      offers: [selectedOffer],
      profile: null,
      company_contacts: null,
      chatActions: {
        read_messages: true,
        send_message: overrides?.canSendMessage ?? true,
        attach_file: overrides?.canSendMessageWithAttachments ?? true,
        mark_messages_received: true,
        mark_messages_read: true,
      },
    },
    contractorInfo: null,
    selectedOffer,
    sortedOffers: [selectedOffer],
    setSelectedOfferId: vi.fn(),
    fileInputRef: { current: null },
    isLoading: false,
    errorMessage: null,
    isChatOpen: true,
    setIsChatOpen: vi.fn(),
    offerDecisionStatus: "" as const,
    isUpdatingOfferStatus: false,
    isUpdatingOfferAmount: false,
    messages: [],
    typingUserIds: [],
    isSending: false,
    canUpload: overrides?.canUpload ?? true,
    canDeleteFile: overrides?.canDeleteFile ?? true,
    canSendMessage: overrides?.canSendMessage ?? true,
    canViewMessages: overrides?.canViewMessages ?? true,
    canSendMessageWithAttachments: overrides?.canSendMessageWithAttachments ?? true,
    canSetReadMessages: true,
    canSetReceivedMessages: true,
    canEditOfferStatus: overrides?.canEditOfferStatus ?? false,
    canEditOfferAmount: overrides?.canEditOfferAmount ?? true,
    canDeleteOwnOffer: overrides?.canDeleteOwnOffer ?? true,
    isContractor: overrides?.isContractor ?? true,
    acceptedOfferId: null,
    offerAmountInput: "120",
    setOfferAmountInput: vi.fn(),
    baselineOfferAmount: "120",
    handleUpload: vi.fn(),
    handleDeleteFile: vi.fn(),
    handleStatusChange: vi.fn(),
    handleOfferAmountSave: vi.fn(),
    handleDeleteOffer: vi.fn(),
    handleCreateNewOffer: vi.fn(),
    onSendMessage: vi.fn(),
    onMessageInputClick: vi.fn(),
    onMessageDraftChange: vi.fn(),
  };
};

describe("OfferWorkspaceView action-driven CTAs", () => {
  const renderWithTheme = () =>
    render(
      <ThemeProvider theme={appTheme}>
        <OfferWorkspaceView />
      </ThemeProvider>
    );

  beforeEach(() => {
    useOfferWorkspaceMock.mockReset();
  });

  it("shows contractor workspace CTAs when backend action flags allow them", () => {
    useOfferWorkspaceMock.mockReturnValue(buildWorkspaceHookState());

    renderWithTheme();

    expect(screen.getByRole("button", { name: "Новый отклик" })).toBeInTheDocument();
    expect(screen.getByTestId("chat-can-send-message")).toHaveTextContent("true");
    expect(screen.getByTestId("chat-can-attach")).toHaveTextContent("true");

    fireEvent.click(screen.getByRole("button", { name: "Изменить" }));

    expect(screen.getByRole("button", { name: "Удалить отклик" })).toBeInTheDocument();
    expect(screen.getByLabelText("Добавить файл")).toBeInTheDocument();
  }, 15_000);

  it("hides contractor workspace CTAs when backend action flags deny them", () => {
    useOfferWorkspaceMock.mockReturnValue(
      buildWorkspaceHookState({
        canUpload: false,
        canDeleteFile: false,
        canSendMessage: false,
        canSendMessageWithAttachments: false,
        canDeleteOwnOffer: false,
        canEditOfferAmount: false,
        createOffer: false,
        offerEditAmount: false,
        offerUploadFile: false,
        offerDeleteFile: false,
        offerDelete: false,
      })
    );

    renderWithTheme();

    expect(screen.queryByRole("button", { name: "Новый отклик" })).not.toBeInTheDocument();
    expect(screen.getByTestId("chat-can-send-message")).toHaveTextContent("false");
    expect(screen.getByTestId("chat-can-attach")).toHaveTextContent("false");

    fireEvent.click(screen.getByRole("button", { name: "Изменить" }));

    expect(screen.queryByRole("button", { name: "Удалить отклик" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Добавить файл")).not.toBeInTheDocument();
  });

  it("shows offer status decision selector only when backend allows accept/reject actions", () => {
    useOfferWorkspaceMock.mockReturnValue(
      buildWorkspaceHookState({
        isContractor: false,
        canEditOfferStatus: true,
        offerAccept: true,
        offerReject: true,
      })
    );

    renderWithTheme();

    expect(screen.getByText("Выберите статус")).toBeInTheDocument();
  });

  it("does not render chat when view_messages is denied", () => {
    useOfferWorkspaceMock.mockReturnValue(
      buildWorkspaceHookState({
        canViewMessages: false,
      })
    );

    renderWithTheme();

    expect(screen.queryByTestId("workspace-chat-panel")).not.toBeInTheDocument();
  });
});
