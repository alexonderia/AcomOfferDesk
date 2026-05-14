import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OfferWorkspacePage } from "@pages/offers/OfferWorkspacePage";

const useAuthMock = vi.fn();

vi.mock("@app/providers/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("@features/offer-workspace", () => ({
  OfferWorkspaceView: () => <div>offer-workspace-view</div>,
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

const renderWorkspacePage = () =>
  render(
    <MemoryRouter
      initialEntries={["/offers/11/workspace"]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/requests" element={<div>requests-page</div>} />
        <Route path="/offers/:id/workspace" element={<OfferWorkspacePage />} />
      </Routes>
    </MemoryRouter>
  );

describe("OfferWorkspacePage", () => {
  beforeEach(() => {
    useAuthMock.mockReset();
  });

  it("renders workspace view when offers.workspace.read permission is present", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: ["offers.workspace.read"],
      },
    });

    renderWorkspacePage();

    expect(screen.getByText("offer-workspace-view")).toBeInTheDocument();
  });

  it("redirects to requests page when offers.workspace.read permission is missing", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: [],
      },
    });

    renderWorkspacePage();

    expect(screen.getByText("requests-page")).toBeInTheDocument();
  });

  it("does not grant workspace access from raw app/delegation claims without atomic permission", () => {
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

    renderWorkspacePage();

    expect(screen.queryByText("offer-workspace-view")).not.toBeInTheDocument();
    expect(screen.getByText("requests-page")).toBeInTheDocument();
  });
});
