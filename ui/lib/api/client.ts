/**
 * API client for Sage Finance OS backend.
 *
 * Uses SWR for client-side data fetching with stale-while-revalidate.
 * All requests proxy through Next.js rewrites → FastAPI backend.
 */

import useSWR, { SWRConfiguration } from "swr";

const API_BASE = "/api";

async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(error.message || `API error: ${res.status}`);
  }
  return res.json();
}

/** Standard API response envelope. */
export interface ApiResponse<T> {
  data: T;
  meta: {
    generated_at: string;
    refreshed_at: string | null;
    is_stale: boolean;
    version: string;
    correlation_id: string | null;
  };
  errors: string[];
}

/** Type-safe SWR hook for API endpoints. */
export function useApi<T>(path: string | null, config?: SWRConfiguration) {
  return useSWR<ApiResponse<T>>(
    path ? `${API_BASE}${path}` : null,
    fetcher,
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
      ...config,
    }
  );
}

/** POST/PUT/DELETE helper. */
export async function apiMutate<T>(
  path: string,
  method: "POST" | "PUT" | "DELETE" = "POST",
  body?: unknown
): Promise<ApiResponse<T>> {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(error.message || `API error: ${res.status}`);
  }

  return res.json();
}
