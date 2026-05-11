import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "@app/providers/AuthProvider";
import { refreshWebSession } from "@shared/api/auth/loginWebUser";
import { setAuthRuntime, setAuthToken } from "@shared/api/client";

vi.mock("@shared/api/auth/loginWebUser", () => ({
  refreshWebSession: vi.fn(),
  logoutWebSession: vi.fn(),
}));

vi.mock("@shared/api/client", () => ({
  setAuthRuntime: vi.fn(),
  setAuthToken: vi.fn(),
}));

const AuthSnapshot = () => {
  const { status, isAuthenticated, session } = useAuth();
  return (
    <div>
      <div data-testid="status">{status}</div>
      <div data-testid="is-authenticated">{String(isAuthenticated)}</div>
      <div data-testid="business-access">{session ? String(session.businessAccess) : "none"}</div>
      <div data-testid="onboarding-state">{session?.onboardingState ?? "none"}</div>
      <div data-testid="permissions">{session?.permissions.join(",") ?? ""}</div>
      <div data-testid="app-roles">{session?.appRoles.join(",") ?? ""}</div>
    </div>
  );
};

const renderProvider = (initialPath = "/") =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <AuthSnapshot />
      </AuthProvider>
    </MemoryRouter>
  );

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("bootstraps authenticated session from refresh endpoint", async () => {
    vi.mocked(refreshWebSession).mockResolvedValue({
      data: {
        access_token: "token-1",
        token_type: "bearer",
        access_token_expires_at: 1_700_000_000,
        user_id: "u-1",
        login: "u-1",
        role_id: 3,
        status: "active",
        auth_provider: "keycloak",
        business_access: true,
        onboarding_state: null,
        permissions: ["requests.read"],
        app_roles: ["app.contractor"],
        delegation_roles: [],
      },
    });

    renderProvider("/requests");

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });

    expect(screen.getByTestId("is-authenticated")).toHaveTextContent("true");
    expect(screen.getByTestId("business-access")).toHaveTextContent("true");
    expect(screen.getByTestId("permissions")).toHaveTextContent("requests.read");
    expect(screen.getByTestId("app-roles")).toHaveTextContent("app.contractor");
    expect(setAuthToken).toHaveBeenCalledWith("token-1");
    expect(setAuthRuntime).toHaveBeenCalled();
  });

  it("exposes anonymous state when bootstrap refresh fails", async () => {
    vi.mocked(refreshWebSession).mockRejectedValue(new Error("unauthorized"));

    renderProvider("/requests");

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    });

    expect(screen.getByTestId("is-authenticated")).toHaveTextContent("false");
    expect(screen.getByTestId("business-access")).toHaveTextContent("none");
    expect(setAuthToken).toHaveBeenCalledWith(null);
  });

  it("keeps business access and onboarding state from backend session payload", async () => {
    vi.mocked(refreshWebSession).mockResolvedValue({
      data: {
        access_token: "token-2",
        token_type: "bearer",
        access_token_expires_at: 1_700_000_100,
        user_id: "u-2",
        login: "u-2",
        role_id: 3,
        status: "review",
        auth_provider: "keycloak",
        business_access: false,
        onboarding_state: "review",
        permissions: ["profile.manage_own"],
        app_roles: ["app.contractor"],
        delegation_roles: [],
      },
    });

    renderProvider("/account");

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });

    expect(screen.getByTestId("business-access")).toHaveTextContent("false");
    expect(screen.getByTestId("onboarding-state")).toHaveTextContent("review");
  });
});
