import { fetchJson } from "../client";
import type { PlanRequestStats } from "./types";

type PlanRequestStatsResponse = {
  data: {
    stats: PlanRequestStats;
  };
};

type GetPlanRequestStatsParams = {
  period?: string;
  dateFrom?: string;
  dateTo?: string;
  planId?: number | null;
};

export const getPlanRequestStats = async ({
  period,
  dateFrom,
  dateTo,
  planId,
}: GetPlanRequestStatsParams): Promise<PlanRequestStats> => {
  const queryParts: string[] = [];
  if (dateFrom && dateTo) {
    queryParts.push(`date_from=${encodeURIComponent(dateFrom)}`);
    queryParts.push(`date_to=${encodeURIComponent(dateTo)}`);
  } else {
    queryParts.push(`period=${encodeURIComponent(period ?? "")}`);
  }
  if (typeof planId === "number") {
    queryParts.push(`plan_id=${planId}`);
  }
  const response = await fetchJson<PlanRequestStatsResponse>(
    `/api/v1/plans/request-stats?${queryParts.join("&")}`,
    { method: "GET" },
    "Не удалось загрузить статистику заявок по плану",
  );
  return response.data.stats;
};
