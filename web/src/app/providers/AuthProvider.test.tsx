import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "@app/providers/AuthProvider";
import { logoutWebSession, refreshWebSession } from "@shared/api/auth/loginWebUser";
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
  const { status, isAuthenticated, session, refresh, logout, beginLogin } = useAuth();
  return (
    <div>
      <div data-testid="status">{status}</div>
      <div data-testid="is-authenticated">{String(isAuthenticated)}</div>
      <div data-testid="business-access">{session ? String(session.businessAccess) : "none"}</div>
      <div data-testid="onboarding-state">{session?.onboardingState ?? "none"}</div>
      <div data-testid="permissions">{session?.permissions.join(",") ?? ""}</div>
      <div data-testid="app-roles">{session?.appRoles.join(",") ?? ""}</div>
      <button type="button" data-testid="refresh-http-401" onClick={() => void refresh("http_401")}>
        refresh-http-401
      </button>
      <button
        type="button"
        data-testid="refresh-http-401-twice"
        onClick={() => void Promise.all([refresh("http_401"), refresh("http_401")])}
      >
        refresh-http-401-twice
      </button>
      <button type="button" data-testid="logout" onClick={logout}>
        logout
      </button>
      <button type="button" data-testid="begin-login-custom" onClick={() => beginLogin("/requests/42")}>
        begin-login-custom
      </button>
    </div>
  );
};

const renderProvider = (initialPath = "/") =>
  render(
    <MemoryRouter
      initialEntries={[initialPath]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
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

  it("switches authenticated session to anonymous on stale refresh failure", async () => {
    vi.mocked(refreshWebSession)
      .mockResolvedValueOnce({
        data: {
          access_token: "token-3",
          token_type: "bearer",
          access_token_expires_at: 1_700_000_200,
          user_id: "u-3",
          login: "u-3",
          role_id: 3,
          status: "active",
          auth_provider: "keycloak",
          business_access: true,
          onboarding_state: null,
          permissions: ["requests.read"],
          app_roles: ["app.contractor"],
          delegation_roles: [],
        },
      })
      .mockRejectedValueOnce(new Error("stale token"));

    renderProvider("/requests");

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });

    fireEvent.click(screen.getByTestId("refresh-http-401"));

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    });

    expect(screen.getByTestId("is-authenticated")).toHaveTextContent("false");
    expect(setAuthToken).toHaveBeenCalledWith(null);
  });

  it("deduplicates repeated refresh and keeps consistent authenticated state", async () => {
    const secondRefreshPayload = {
      data: {
        access_token: "token-5",
        token_type: "bearer",
        access_token_expires_at: 1_700_000_400,
        user_id: "u-4",
        login: "u-4",
        role_id: 3,
        status: "active",
        auth_provider: "keycloak",
        business_access: true,
        onboarding_state: null,
        permissions: ["requests.read"],
        app_roles: ["app.contractor"],
        delegation_roles: [],
      },
    };
    let releaseSecondRefresh!: () => void;
    const secondRefreshPromise = new Promise<typeof secondRefreshPayload>((resolve) => {
      releaseSecondRefresh = () => resolve(secondRefreshPayload);
    });

    vi.mocked(refreshWebSession)
      .mockResolvedValueOnce({
        data: {
          access_token: "token-4",
          token_type: "bearer",
          access_token_expires_at: 1_700_000_300,
          user_id: "u-4",
          login: "u-4",
          role_id: 3,
          status: "active",
          auth_provider: "keycloak",
          business_access: true,
          onboarding_state: null,
          permissions: ["requests.read"],
          app_roles: ["app.contractor"],
          delegation_roles: [],
        },
      })
      .mockImplementationOnce(() => secondRefreshPromise);

    renderProvider("/requests");

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });

    fireEvent.click(screen.getByTestId("refresh-http-401-twice"));

    await waitFor(() => {
      expect(refreshWebSession).toHaveBeenCalledTimes(2);
    });

    releaseSecondRefresh();

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });

    expect(screen.getByTestId("is-authenticated")).toHaveTextContent("true");
    expect(setAuthToken).toHaveBeenCalledWith("token-5");
  });

  it("clears token and runtime on logout", async () => {
    vi.mocked(refreshWebSession).mockResolvedValue({
      data: {
        access_token: "token-6",
        token_type: "bearer",
        access_token_expires_at: 1_700_000_500,
        user_id: "u-6",
        login: "u-6",
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

    fireEvent.click(screen.getByTestId("logout"));

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    });

    expect(logoutWebSession).toHaveBeenCalledTimes(1);
    expect(setAuthToken).toHaveBeenCalledWith(null);
  });

  it("uses explicit deep-link target in beginLogin redirect url", async () => {
    const assignSpy = vi.fn();
    vi.stubGlobal("location", { assign: assignSpy } as unknown as Location);
    try {
      vi.mocked(refreshWebSession).mockRejectedValue(new Error("unauthorized"));

      renderProvider("/requests");

      await waitFor(() => {
        expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
      });

      fireEvent.click(screen.getByTestId("begin-login-custom"));

      expect(assignSpy).toHaveBeenCalledWith("/api/v1/auth/oidc/login?next_path=%2Frequests%2F42");
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
