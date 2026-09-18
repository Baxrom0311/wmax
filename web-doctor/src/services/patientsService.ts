import { getMockPatientDetail, MOCK_PATIENTS } from "../lib/mock";
import type { AlertLevel, PatientDetail, PatientSummary } from "../lib/types";
import { apiClient } from "./apiClient";

export interface PatientFilterParams {
  district?: string | null;
  level?: AlertLevel | null;
}

export const patientsService = {
  async list(filters?: PatientFilterParams): Promise<PatientSummary[]> {
    const params = new URLSearchParams();
    if (filters?.district) params.set("district", filters.district);
    if (filters?.level) params.set("level", filters.level);

    const qs = params.toString();
    const endpoint = `/api/v1/patients${qs ? `?${qs}` : ""}`;

    try {
      return await apiClient<PatientSummary[]>(endpoint);
    } catch {
      // Fallback to mock for offline / demo
      let filtered = [...MOCK_PATIENTS];
      if (filters?.district) {
        filtered = filtered.filter((p) => p.district === filters.district);
      }
      if (filters?.level) {
        filtered = filtered.filter((p) => p.level === filters.level);
      }
      return filtered;
    }
  },

  async getById(id: string, days = 7): Promise<PatientDetail> {
    try {
      return await apiClient<PatientDetail>(`/api/v1/patients/${encodeURIComponent(id)}?days=${days}`);
    } catch {
      return getMockPatientDetail(id);
    }
  },

  async approveBaseline(id: string): Promise<void> {
    try {
      await apiClient(`/api/v1/patients/${encodeURIComponent(id)}/approve-baseline`, {
        method: "POST",
      });
    } catch {
      // Fallback
    }
  },

  async discharge(id: string): Promise<void> {
    try {
      await apiClient(`/api/v1/patients/${encodeURIComponent(id)}/discharge`, {
        method: "POST",
      });
    } catch {
      // Fallback
    }
  },
};
