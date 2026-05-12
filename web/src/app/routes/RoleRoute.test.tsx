import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RoleRoute } from "@app/routes/RoleRoute";

const useAuthMock = vi.fn();

vi.mock("@app/providers/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
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

const renderRoleRoute = (path: string, element: JSX.Element) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/login" element={<div>login-page</div>} />
        <Route path="/account" element={<div>account-page</div>} />
        <Route path="/requests" element={<div>requests-page</div>} />
        <Route path="/admin" element={element} />
      </Routes>
    </MemoryRouter>
  );

describe("RoleRoute", () => {
  beforeEach(() => {
    useAuthMock.mockReset();
  });

  it("redirects to login when session is absent", () => {
    useAuthMock.mockReturnValue({ session: null });

    renderRoleRoute(
      "/admin",
      <RoleRoute allowedPermissions={["users.read"]}>
        <div>admin-page</div>
      </RoleRoute>
    );

    expect(screen.getByText("login-page")).toBeInTheDocument();
  });

  it("redirects to account when business access is disabled", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        businessAccess: false,
      },
    });

    renderRoleRoute(
      "/admin",
      <RoleRoute allowedPermissions={["users.read"]}>
        <div>admin-page</div>
      </RoleRoute>
    );

    expect(screen.getByText("account-page")).toBeInTheDocument();
  });

  it("allows route access when required permission is present", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: ["users.read"],
      },
    });

    renderRoleRoute(
      "/admin",
      <RoleRoute allowedPermissions={["users.read"]}>
        <div>admin-page</div>
      </RoleRoute>
    );

    expect(screen.getByText("admin-page")).toBeInTheDocument();
  });

  it("redirects to role default path when required permission is missing", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: [],
      },
    });

    renderRoleRoute(
      "/admin",
      <RoleRoute allowedPermissions={["users.read"]}>
        <div>admin-page</div>
      </RoleRoute>
    );

    expect(screen.getByText("requests-page")).toBeInTheDocument();
  });

  it("does not grant route access from raw app/delegation claims without permission", () => {
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

    renderRoleRoute(
      "/admin",
      <RoleRoute allowedPermissions={["users.read"]}>
        <div>admin-page</div>
      </RoleRoute>
    );

    expect(screen.queryByText("admin-page")).not.toBeInTheDocument();
    expect(screen.getByText("requests-page")).toBeInTheDocument();
  });
});
