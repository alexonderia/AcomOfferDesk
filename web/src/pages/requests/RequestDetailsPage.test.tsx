import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RequestDetailsPage } from "@pages/requests/RequestDetailsPage";

const useAuthMock = vi.fn();

vi.mock("@app/providers/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("@features/request-details", () => ({
  RequestDetailsView: () => <div>request-details-view</div>,
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
  authProvider: "iam",
  businessAccess: true,
  onboardingState: null,
  permissions: [] as string[],
  appRoles: [] as string[],
  delegationRoles: [] as string[],
};

const renderDetailsPage = () =>
  render(
    <MemoryRouter
      initialEntries={["/requests/17"]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/requests" element={<div>requests-page</div>} />
        <Route path="/requests/:id" element={<RequestDetailsPage />} />
      </Routes>
    </MemoryRouter>
  );

describe("RequestDetailsPage", () => {
  beforeEach(() => {
    useAuthMock.mockReset();
  });

  it("renders details view when requests.read permission is present", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: ["requests.read"],
      },
    });

    renderDetailsPage();

    expect(screen.getByText("request-details-view")).toBeInTheDocument();
  });

  it("renders details view when department.requests.read permission is present", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: ["department.requests.read"],
      },
    });

    renderDetailsPage();

    expect(screen.getByText("request-details-view")).toBeInTheDocument();
  });

  it("redirects to requests page when permissions are missing", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: [],
      },
    });

    renderDetailsPage();

    expect(screen.getByText("requests-page")).toBeInTheDocument();
  });
});
