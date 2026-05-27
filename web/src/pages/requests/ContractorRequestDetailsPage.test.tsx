import { ThemeProvider } from "@mui/material/styles";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ContractorRequestDetailsPage } from "@pages/requests/ContractorRequestDetailsPage";
import { getContractorRequestView } from "@shared/api/requests/getContractorRequestView";
import { appTheme } from "@shared/theme/appTheme";

const useAuthMock = vi.fn();

vi.mock("@app/providers/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("@shared/api/requests/getContractorRequestView", () => ({
  getContractorRequestView: vi.fn(),
}));

vi.mock("@shared/api/offers/createOfferForRequest", () => ({
  createOfferForRequest: vi.fn(),
}));

vi.mock("@shared/api/fileDownload", () => ({
  downloadFile: vi.fn(),
}));

vi.mock("@features/request-details/ui/RequestDetailsMainCard", () => ({
  RequestDetailsMainCard: () => <div data-testid="request-details-main-card" />,
}));

const baseSession = {
  token: "token",
  tokenType: "bearer",
  tokenExpiresAt: 1_700_000_000,
  userId: "u-1",
  login: "u-1",
  roleId: 3,
  role: "contractor",
  status: "active",
  authProvider: "keycloak",
  businessAccess: true,
  onboardingState: null,
  permissions: [] as string[],
  appRoles: [] as string[],
  delegationRoles: [] as string[],
};

const baseRequestView = {
  id: 17,
  description: "Request details",
  status: "open",
  status_label: "Open",
  deadline_at: "2026-05-20T00:00:00Z",
  updated_at: "2026-05-20T00:00:00Z",
  owner_user_id: "owner-1",
  owner_full_name: "Owner One",
  files: [],
  existing_offer: null,
  actions: {
    view_details: true,
    view_amounts: false,
    open_contractor_view: true,
    edit: false,
    update_status: false,
    change_owner: false,
    upload_file: false,
    delete_file: false,
    send_email_notifications: false,
    mark_deleted_alert_viewed: false,
    create_offer: true,
  },
};

const renderPage = () =>
  render(
    <ThemeProvider theme={appTheme}>
      <MemoryRouter
        initialEntries={["/requests/17/contractor"]}
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <Routes>
          <Route path="/requests" element={<div>requests-page</div>} />
          <Route path="/requests/:id/contractor" element={<ContractorRequestDetailsPage />} />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>
  );

describe("ContractorRequestDetailsPage", () => {
  beforeEach(() => {
    useAuthMock.mockReset();
    vi.mocked(getContractorRequestView).mockReset();
  });

  it("redirects to requests page when requests.contractor_view.read permission is missing", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: [],
      },
    });

    vi.mocked(getContractorRequestView).mockResolvedValue(baseRequestView as never);

    renderPage();

    expect(screen.getByText("requests-page")).toBeInTheDocument();
  });

  it("shows create-offer CTA when backend action create_offer=true", async () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: ["requests.contractor_view.read"],
      },
    });

    vi.mocked(getContractorRequestView).mockResolvedValue({
      ...baseRequestView,
      actions: {
        ...baseRequestView.actions,
        create_offer: true,
      },
    } as never);

    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("request-details-main-card")).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Откликнуться" })).toBeInTheDocument();
  }, 15_000);

  it("hides create-offer CTA when backend action create_offer=false", async () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: ["requests.contractor_view.read"],
      },
    });

    vi.mocked(getContractorRequestView).mockResolvedValue({
      ...baseRequestView,
      actions: {
        ...baseRequestView.actions,
        create_offer: false,
      },
    } as never);

    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("request-details-main-card")).toBeInTheDocument();
    });

    expect(screen.queryByRole("button", { name: "Откликнуться" })).not.toBeInTheDocument();
  });

  it("does not grant contractor-view access from raw app/delegation claims without atomic permission", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        roleId: 1,
        role: "superadmin",
        permissions: [],
        appRoles: ["app.superadmin"],
        delegationRoles: ["delegation.any"],
      },
    });

    vi.mocked(getContractorRequestView).mockResolvedValue(baseRequestView as never);

    renderPage();

    expect(screen.getByText("requests-page")).toBeInTheDocument();
  });
});
