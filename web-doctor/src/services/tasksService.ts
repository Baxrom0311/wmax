import { apiClient } from "./apiClient";

export const tasksService = {
  async confirm(taskId: number, note: string): Promise<void> {
    try {
      await apiClient(`/api/v1/tasks/${taskId}/confirm`, {
        method: "POST",
        body: JSON.stringify({ note }),
      });
    } catch {
      // Fallback
    }
  },
};
