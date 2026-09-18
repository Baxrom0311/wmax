import { useQuery } from "@tanstack/react-query";
import { useFilterStore } from "../stores/filterStore";
import type { AlertLevel, PatientSummary } from "../lib/types";
import { patientsService } from "../services/patientsService";

export function usePatients() {
  const { district, level } = useFilterStore();

  const query = useQuery<PatientSummary[], Error>({
    queryKey: ["patients", district, level],
    queryFn: () =>
      patientsService.list({ district, level: level as AlertLevel | null }),
    staleTime: 30_000, // 30 seconds
    gcTime: 5 * 60_000, // 5 minutes
    retry: 2,
    refetchInterval: 60_000, // auto-refresh every 1 minute
  });

  return query;
}
