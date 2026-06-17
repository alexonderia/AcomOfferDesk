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
    <MemoryRouter
      initialEntries={[path]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/login" element={<div>login-page</div>} />
        <Route path="/account" element={<div>account-page</div>} />
        <Route path="/requests" element={<div>requests-page</div>} />
        <Route path="/admin" element={path === "/admin" ? element : <div>admin-page</div>} />
        <Route path="/contractors" element={path === "/contractors" ? element : <div>contractors-page</div>} />
        <Route path="/feedback" element={path === "/feedback" ? element : <div>feedback-page</div>} />
        <Route path="/pm-dashboard" element={path === "/pm-dashboard" ? element : <div>pm-dashboard-page</div>} />
        <Route
          path="/pm-dashboard/savings"
          element={path === "/pm-dashboard/savings" ? element : <div>pm-dashboard-savings-page</div>}
        />
        <Route
          path="/pm-dashboard/plan"
          element={path === "/pm-dashboard/plan" ? element : <div>pm-dashboard-plan-page</div>}
        />
      </Routes>
    </MemoryRouter>
  );

const guardedCases = [
  { path: "/admin", permission: "users.read", pageText: "admin-page" },
  { path: "/contractors", permission: "contractors.read", pageText: "contractors-page" },
  { path: "/feedback", permission: "feedback.read", pageText: "feedback-page" },
  { path: "/pm-dashboard", permission: "dashboard.process.read", pageText: "pm-dashboard-page" },
  { path: "/pm-dashboard/savings", permission: "dashboard.savings.read", pageText: "pm-dashboard-savings-page" },
  { path: "/pm-dashboard/plan", permission: "dashboard.plans.read", pageText: "pm-dashboard-plan-page" },
] as const;

describe("RoleRoute", () => {
  beforeEach(() => {
    useAuthMock.mockReset();
  });

  it.each(guardedCases)("redirects to login when session is absent for $path", ({ path, permission, pageText }) => {
    useAuthMock.mockReturnValue({ session: null });

    renderRoleRoute(
      path,
      <RoleRoute allowedPermissions={[permission]}>
        <div>{pageText}</div>
      </RoleRoute>
    );

    expect(screen.getByText("login-page")).toBeInTheDocument();
  });

  it.each(guardedCases)(
    "redirects to account when business access is disabled for $path",
    ({ path, permission, pageText }) => {
      useAuthMock.mockReturnValue({
        session: {
          ...baseSession,
          businessAccess: false,
        },
      });

      renderRoleRoute(
        path,
        <RoleRoute allowedPermissions={[permission]}>
          <div>{pageText}</div>
        </RoleRoute>
      );

      expect(screen.getByText("account-page")).toBeInTheDocument();
    }
  );

  it.each(guardedCases)("allows route access when required permission is present for $path", ({ path, permission, pageText }) => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: [permission],
      },
    });

    renderRoleRoute(
      path,
      <RoleRoute allowedPermissions={[permission]}>
        <div>{pageText}</div>
      </RoleRoute>
    );

    expect(screen.getByText(pageText)).toBeInTheDocument();
  });

  it.each(guardedCases)(
    "redirects to role default path when required permission is missing for $path",
    ({ path, permission, pageText }) => {
      useAuthMock.mockReturnValue({
        session: {
          ...baseSession,
          permissions: [],
        },
      });

      renderRoleRoute(
        path,
        <RoleRoute allowedPermissions={[permission]}>
          <div>{pageText}</div>
        </RoleRoute>
      );

      expect(screen.queryByText(pageText)).not.toBeInTheDocument();
      expect(screen.getByText("account-page")).toBeInTheDocument();
    }
  );

  it("redirects administrator without feedback.read to /admin when users.read is present", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        roleId: 2,
        role: "admin",
        permissions: ["users.read"],
      },
    });

    renderRoleRoute(
      "/feedback",
      <RoleRoute allowedPermissions={["feedback.read"]}>
        <div>feedback-page</div>
      </RoleRoute>
    );

    expect(screen.queryByText("feedback-page")).not.toBeInTheDocument();
    expect(screen.getByText("admin-page")).toBeInTheDocument();
  });

  it.each(guardedCases)(
    "does not grant access from raw app/delegation claims without permission for $path",
    ({ path, permission, pageText }) => {
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
        path,
        <RoleRoute allowedPermissions={[permission]}>
          <div>{pageText}</div>
        </RoleRoute>
      );

      expect(screen.queryByText(pageText)).not.toBeInTheDocument();
      expect(screen.getByText("account-page")).toBeInTheDocument();
    }
  );

  it("allows route access when any permission from allowedPermissions is present", () => {
    useAuthMock.mockReturnValue({
      session: {
        ...baseSession,
        permissions: ["department.dashboard.read"],
      },
    });

    renderRoleRoute(
      "/pm-dashboard",
      <RoleRoute allowedPermissions={["dashboard.process.read", "department.dashboard.read"]}>
        <div>pm-dashboard-page</div>
      </RoleRoute>
    );

    expect(screen.getByText("pm-dashboard-page")).toBeInTheDocument();
  });
});
