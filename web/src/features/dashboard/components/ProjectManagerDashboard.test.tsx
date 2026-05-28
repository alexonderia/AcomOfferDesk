import { ThemeProvider } from "@mui/material/styles";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectManagerDashboard } from "@features/dashboard/components/ProjectManagerDashboard";
import { getResponsibilityDashboard } from "@shared/api/users/getResponsibilityDashboard";
import { appTheme } from "@shared/theme/appTheme";

vi.mock("@shared/api/users/getResponsibilityDashboard", () => ({
  getResponsibilityDashboard: vi.fn(),
}));

vi.mock("@app/providers/AuthProvider", () => ({
  useAuth: () => ({
    session: {
      roleId: 5,
      userId: "lead-1",
    },
  }),
}));

vi.mock("@features/dashboard/components/DashboardCharts", () => ({
  CircularProcessChart: () => <div data-testid="dashboard-process-chart" />,
  EmployeeWorkloadChart: () => <div data-testid="dashboard-workload-chart" />,
}));

vi.mock("@features/dashboard/components/EmployeeNodeCard", () => ({
  EmployeeNodeCard: () => <div data-testid="employee-node-card" />,
}));

const showErrorToastMock = vi.fn();
const showSuccessToastMock = vi.fn();

vi.mock("@shared/ui/toasts", () => ({
  useSystemToasts: () => ({
    showErrorToast: showErrorToastMock,
    showSuccessToast: showSuccessToastMock,
  }),
}));

vi.mock("@shared/lib/responsive", () => ({
  useIsMobileViewport: () => false,
}));

const baseDashboardPayload = {
  tree: [],
  unassignedRequests: [],
  myRequests: [],
  assignedRequests: [],
  activeUnavailability: [],
  upcomingUnavailability: [],
  savings: {
    total_closed_requests: 0,
    total_with_savings: 0,
    total_savings_amount: 0,
    closed_items: [],
    items: [],
  },
};

const renderWithTheme = () =>
  render(
    <ThemeProvider theme={appTheme}>
      <ProjectManagerDashboard />
    </ThemeProvider>
  );

describe("ProjectManagerDashboard widget states", () => {
  beforeEach(() => {
    vi.mocked(getResponsibilityDashboard).mockReset();
    showErrorToastMock.mockReset();
    showSuccessToastMock.mockReset();
  });

  it("renders loading state while dashboard request is pending", () => {
    vi.mocked(getResponsibilityDashboard).mockReturnValue(new Promise(() => undefined) as never);

    renderWithTheme();

    expect(screen.getByText("Загрузка...")).toBeInTheDocument();
  });

  it("renders empty state when there are no subordinate employees", async () => {
    vi.mocked(getResponsibilityDashboard).mockResolvedValue(baseDashboardPayload as never);

    renderWithTheme();

    await waitFor(() => {
      expect(screen.getByText("Подчинённые сотрудники не найдены")).toBeInTheDocument();
    });
  });

  it("renders error state when dashboard API call fails", async () => {
    vi.mocked(getResponsibilityDashboard).mockRejectedValue(new Error("dashboard failed"));

    renderWithTheme();

    await waitFor(() => {
      expect(showErrorToastMock).toHaveBeenCalledWith("dashboard failed");
    });
  });
});
