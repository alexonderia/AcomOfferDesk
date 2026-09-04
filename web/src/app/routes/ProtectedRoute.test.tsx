import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProtectedRoute } from "@app/routes/ProtectedRoute";

const useAuthMock = vi.fn();

vi.mock("@app/providers/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

const renderProtectedRoutes = (path: string) =>
  render(
    <MemoryRouter
      initialEntries={[path]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/login" element={<div>login-page</div>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/protected" element={<div>protected-page</div>} />
          <Route path="/requests" element={<div>requests-page</div>} />
          <Route path="/requests/:id/contractor" element={<div>contractor-request-page</div>} />
          <Route path="/offers/:id/workspace" element={<div>offer-workspace-page</div>} />
          <Route path="/account" element={<div>account-page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );

describe("ProtectedRoute", () => {
  beforeEach(() => {
    useAuthMock.mockReset();
  });

  it.each(["/protected", "/requests", "/requests/17/contractor", "/offers/11/workspace"])(
    "redirects anonymous users to login for %s",
    (path) => {
      useAuthMock.mockReturnValue({
        status: "unauthenticated",
        isAuthenticated: false,
        session: null,
      });

      renderProtectedRoutes(path);

      expect(screen.getByText("login-page")).toBeInTheDocument();
    }
  );

  it.each(["/protected", "/requests", "/requests/17/contractor", "/offers/11/workspace"])(
    "redirects users without business access to account page for %s",
    (path) => {
      useAuthMock.mockReturnValue({
        status: "authenticated",
        isAuthenticated: true,
        session: {
          businessAccess: false,
        },
      });

      renderProtectedRoutes(path);

      expect(screen.getByText("account-page")).toBeInTheDocument();
    }
  );

  it("renders child route for authenticated user with business access", () => {
    useAuthMock.mockReturnValue({
      status: "authenticated",
      isAuthenticated: true,
      session: {
        businessAccess: true,
      },
    });

    renderProtectedRoutes("/protected");

    expect(screen.getByText("protected-page")).toBeInTheDocument();
  });

  it("keeps the protected URL and shows controlled unavailability", () => {
    useAuthMock.mockReturnValue({
      status: "unavailable",
      isAuthenticated: false,
      session: null,
    });

    renderProtectedRoutes("/protected");

    expect(screen.getByRole("button", { name: "Обновить страницу" })).toBeInTheDocument();
  });
});
