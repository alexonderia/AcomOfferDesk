import { ThemeProvider } from "@mui/material/styles";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectManagerDashboard } from "@features/dashboard/components/ProjectManagerDashboard";
import { getUnitsTree } from "@shared/api/units";
import { getResponsibilityDashboard } from "@shared/api/users/getResponsibilityDashboard";
import { ROLE } from "@shared/constants/roles";
import { appTheme } from "@shared/theme/appTheme";

vi.mock("@shared/api/units", () => ({
  getUnitsTree: vi.fn(),
}));

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
  EmployeeNodeCard: ({ node }: { node: { user_id: string } }) => <div>{`employee-card:${node.user_id}`}</div>,
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
    vi.mocked(getUnitsTree).mockReset();
    showErrorToastMock.mockReset();
    showSuccessToastMock.mockReset();
    vi.mocked(getUnitsTree).mockResolvedValue([] as never);
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

  it("filters only the workload block by department", async () => {
    vi.mocked(getResponsibilityDashboard).mockResolvedValue({
      ...baseDashboardPayload,
      tree: [
        {
          user_id: "lead-a",
          full_name: "Lead A",
          role_id: 4,
          role_name: "Руководитель проекта",
          parent_user_id: null,
          in_progress_total: 1,
          statuses: [],
          children: [],
        },
        {
          user_id: "lead-b",
          full_name: "Lead B",
          role_id: 4,
          role_name: "Руководитель проекта",
          parent_user_id: null,
          in_progress_total: 1,
          statuses: [],
          children: [],
        },
      ],
      assignedRequests: [
        {
          request_id: "101",
          description: "Request",
          status: "open",
          status_label: "Открыта",
          deadline_at: "2026-07-01T00:00:00Z",
          created_at: "2026-07-01T00:00:00Z",
          updated_at: "2026-07-01T00:00:00Z",
          owner_user_id: "lead-a",
          owner_full_name: "Lead A",
        },
      ],
    } as never);
    vi.mocked(getUnitsTree).mockResolvedValue([
      {
        unit_id: 1,
        name: "АО 1",
        id_parent: null,
        is_active: true,
        members: [
          {
            user_id: "lead-a",
            full_name: "Lead A",
            role_id: 4,
            role_name: "Руководитель проекта",
            status: "active",
            id_parent_user: null,
          },
        ],
        children: [],
        actions: {
          canCreateChild: false,
          canUpdate: false,
          canDelete: false,
          canManageMembers: false,
        },
      },
      {
        unit_id: 2,
        name: "АО 2",
        id_parent: null,
        is_active: true,
        members: [
          {
            user_id: "lead-b",
            full_name: "Lead B",
            role_id: 4,
            role_name: "Руководитель проекта",
            status: "active",
            id_parent_user: null,
          },
        ],
        children: [],
        actions: {
          canCreateChild: false,
          canUpdate: false,
          canDelete: false,
          canManageMembers: false,
        },
      },
    ] as never);

    renderWithTheme();

    await waitFor(() => {
      expect(screen.getByText("employee-card:lead-a")).toBeInTheDocument();
      expect(screen.getByText("employee-card:lead-b")).toBeInTheDocument();
    });

    fireEvent.mouseDown(screen.getByRole("combobox"));
    fireEvent.click(await screen.findByText("АО 1"));

    await waitFor(() => {
      expect(screen.getByText("employee-card:lead-a")).toBeInTheDocument();
      expect(screen.queryByText("employee-card:lead-b")).not.toBeInTheDocument();
    });

    expect(screen.getByText("Распределённые (1)")).toBeInTheDocument();
  });

  it("uses child units for workload display instead of root department members when the department has nested units", async () => {
    vi.mocked(getResponsibilityDashboard).mockResolvedValue({
      ...baseDashboardPayload,
      tree: [
        {
          user_id: "root-pm",
          full_name: "Root PM",
          role_id: 4,
          role_name: "Руководитель проекта",
          parent_user_id: null,
          in_progress_total: 1,
          statuses: [],
          children: [],
        },
        {
          user_id: "olga",
          full_name: "Olga",
          role_id: ROLE.LEAD_ECONOMIST,
          role_name: "Ведущий экономист",
          parent_user_id: null,
          in_progress_total: 1,
          statuses: [],
          children: [],
        },
      ],
    } as never);
    vi.mocked(getUnitsTree).mockResolvedValue([
      {
        unit_id: 1,
        name: "УЭ",
        id_parent: null,
        is_active: true,
        members: [
          {
            user_id: "root-pm",
            full_name: "Root PM",
            role_id: 4,
            role_name: "Руководитель проекта",
            status: "active",
            id_parent_user: null,
          },
        ],
        children: [
          {
            unit_id: 2,
            name: "Модуль 2.1",
            id_parent: 1,
            is_active: true,
            members: [
              {
                user_id: "olga",
                full_name: "Olga",
                role_id: ROLE.LEAD_ECONOMIST,
                role_name: "Ведущий экономист",
                status: "active",
                id_parent_user: null,
              },
            ],
            children: [],
            actions: {
              canCreateChild: false,
              canUpdate: false,
              canDelete: false,
              canManageMembers: false,
            },
          },
        ],
        actions: {
          canCreateChild: false,
          canUpdate: false,
          canDelete: false,
          canManageMembers: false,
        },
      },
    ] as never);

    renderWithTheme();

    await waitFor(() => {
      expect(screen.getByText("employee-card:olga")).toBeInTheDocument();
    });

    expect(screen.queryByText("employee-card:root-pm")).not.toBeInTheDocument();
  });
});
