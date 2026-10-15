import { ThemeProvider } from "@mui/material/styles";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectManagerSavingsDashboard } from "@features/dashboard/components/ProjectManagerSavingsDashboard";
import { getResponsibilityDashboard } from "@shared/api/users/getResponsibilityDashboard";
import { appTheme } from "@shared/theme/appTheme";

vi.mock("@shared/api/users/getResponsibilityDashboard", () => ({
  getResponsibilityDashboard: vi.fn(),
}));

const emptySavingsPayload = {
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
      <ProjectManagerSavingsDashboard />
    </ThemeProvider>
  );

describe("ProjectManagerSavingsDashboard widget states", () => {
  beforeEach(() => {
    vi.mocked(getResponsibilityDashboard).mockReset();
  });

  it("renders loading state while savings API call is pending", async () => {
    vi.mocked(getResponsibilityDashboard).mockReturnValue(new Promise(() => undefined) as never);

    renderWithTheme();

    await waitFor(() => {
      expect(screen.getByText("Загрузка...")).toBeInTheDocument();
    });
  }, 15_000);

  it("renders empty state widgets for empty savings payload", async () => {
    vi.mocked(getResponsibilityDashboard).mockResolvedValue(emptySavingsPayload as never);

    renderWithTheme();

    await waitFor(() => {
      expect(screen.getByText("Пока нет закрытых заявок с рассчитанной экономией.")).toBeInTheDocument();
    });
  });

  it("renders error state when savings API call fails", async () => {
    vi.mocked(getResponsibilityDashboard).mockRejectedValue(new Error("savings failed"));

    renderWithTheme();

    await waitFor(() => {
      expect(screen.getByText("savings failed")).toBeInTheDocument();
    });
  });

  it("does not render NaN/undefined/Infinity in summary values", async () => {
    vi.mocked(getResponsibilityDashboard).mockResolvedValue(emptySavingsPayload as never);

    renderWithTheme();

    await waitFor(() => {
      expect(screen.getByText("Экономия")).toBeInTheDocument();
    });

    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Infinity/)).not.toBeInTheDocument();
    expect(screen.queryByText(/undefined/)).not.toBeInTheDocument();
  });

  it("renders zero for closed requests without applicable savings", async () => {
    vi.mocked(getResponsibilityDashboard).mockResolvedValue({
      ...emptySavingsPayload,
      savings: {
        ...emptySavingsPayload.savings,
        total_closed_requests: 1,
        closed_items: [
          {
            request_id: "above-initial",
            owner_user_id: "econ-1",
            owner_full_name: "Экономист",
            initial_amount: 1_000_000,
            offer_amount: 1_850_000,
            final_amount: 1_000_000,
            savings_amount: 0,
            // Period filter defaults to the current month; a hardcoded date
            // silently falls out of the filter as months pass (Sept 2026).
            // toLocaleDateString('sv-SE') → local YYYY-MM-DD (matches dateFrom/dateTo).
            closed_at: new Date().toLocaleDateString("sv-SE"),
            plan_id: null,
            plan_name: null,
          },
        ],
      },
    } as never);

    renderWithTheme();

    await waitFor(() => {
      expect(screen.getByText("Заявка #above-initial")).toBeInTheDocument();
    });

    expect(screen.getAllByText("0,00 ₽")).toHaveLength(3);
  });
});
