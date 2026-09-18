import { useAuthStore } from "../stores/authStore";

export class ApiError extends Error {
  constructor(public status: number, message: string, public data?: unknown) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = useAuthStore.getState().token;
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    useAuthStore.getState().logout();
    throw new ApiError(401, "Sessiya tugagan yoki ruxsat yo'q");
  }

  if (!response.ok) {
    let errorDetail = `So'rovda xatolik: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson?.detail) {
        errorDetail = errorJson.detail;
      }
    } catch {
      // fallback to status text
    }
    throw new ApiError(response.status, errorDetail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return (await response.json()) as T;
}
