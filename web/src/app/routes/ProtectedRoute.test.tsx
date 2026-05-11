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
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/login" element={<div>login-page</div>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/protected" element={<div>protected-page</div>} />
          <Route path="/account" element={<div>account-page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );

describe("ProtectedRoute", () => {
  beforeEach(() => {
    useAuthMock.mockReset();
  });

  it("redirects anonymous users to login", () => {
    useAuthMock.mockReturnValue({
      status: "anonymous",
      isAuthenticated: false,
      session: null,
    });

    renderProtectedRoutes("/protected");

    expect(screen.getByText("login-page")).toBeInTheDocument();
  });

  it("redirects users without business access to account page", () => {
    useAuthMock.mockReturnValue({
      status: "authenticated",
      isAuthenticated: true,
      session: {
        businessAccess: false,
      },
    });

    renderProtectedRoutes("/protected");

    expect(screen.getByText("account-page")).toBeInTheDocument();
  });

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

  it("shows loading spinner during bootstrapping", () => {
    useAuthMock.mockReturnValue({
      status: "bootstrapping",
      isAuthenticated: false,
      session: null,
    });

    renderProtectedRoutes("/protected");

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });
});
