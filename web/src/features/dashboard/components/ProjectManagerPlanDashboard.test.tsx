import { ThemeProvider } from "@mui/material/styles";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectManagerPlanDashboard } from "@features/dashboard/components/ProjectManagerPlanDashboard";
import { appTheme } from "@shared/theme/appTheme";

const usePlanDashboardMock = vi.fn();

vi.mock("@features/dashboard/model/usePlanDashboard", () => ({
  usePlanDashboard: () => usePlanDashboardMock(),
}));

vi.mock("@app/providers/AuthProvider", () => ({
  useAuth: () => ({
    session: {
      userId: "manager-1",
    },
  }),
}));

vi.mock("@features/dashboard/components/plan/PlanOverviewSections", () => ({
  PlanAnalyticsCards: () => <div data-testid="plan-analytics-cards" />,
  PlanKpiRow: () => <div data-testid="plan-kpi-row" />,
  PlanPageHeader: () => <div data-testid="plan-page-header" />,
  planSectionCardSx: {},
}));

vi.mock("@features/dashboard/components/plan/PlanHierarchySection", () => ({
  PlanHierarchySection: () => <div data-testid="plan-hierarchy-section" />,
}));

vi.mock("@features/dashboard/components/plan/PlanDialogs", () => ({
  PlanDialogs: () => <div data-testid="plan-dialogs" />,
}));

const buildPlanDashboardState = (overrides?: Partial<Record<string, unknown>>) => ({
  period: "2026-05",
  setPeriod: vi.fn(),
  setDateFrom: vi.fn(),
  setDateTo: vi.fn(),
  trees: [],
  summary: {
    total_plan_amount: 0,
    total_fact_amount: 0,
    total_progress_percent: 0,
    total_remaining_amount: 0,
  },
  requestStats: null,
  isLoading: false,
  isMutating: false,
  canCreateRootPlan: false,
  rootPlanExists: false,
  errorMessage: null,
  successMessage: null,
  setSuccessMessage: vi.fn(),
  createRoot: vi.fn(),
  createSubplanNodeWithStart: vi.fn(),
  delegate: vi.fn(),
  updatePlanNode: vi.fn(),
  removeChildPlan: vi.fn(),
  closePlanNode: vi.fn(),
  loadDelegateCandidates: vi.fn().mockResolvedValue([]),
  ...overrides,
});

const renderWithTheme = () =>
  render(
    <ThemeProvider theme={appTheme}>
      <ProjectManagerPlanDashboard />
    </ThemeProvider>
  );

describe("ProjectManagerPlanDashboard widget states", () => {
  beforeEach(() => {
    usePlanDashboardMock.mockReset();
  });

  it("renders empty-state card when root plan does not exist", () => {
    usePlanDashboardMock.mockReturnValue(buildPlanDashboardState());

    renderWithTheme();

    expect(screen.getByText("План на выбранный период еще не создан")).toBeInTheDocument();
  });

  it("renders error state when hook exposes loading error", () => {
    usePlanDashboardMock.mockReturnValue(
      buildPlanDashboardState({
        errorMessage: "plan failed",
      })
    );

    renderWithTheme();

    expect(screen.getByText("plan failed")).toBeInTheDocument();
  });
});
