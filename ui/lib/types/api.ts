export type { ApiResponse } from "@/lib/api/client";

export interface PaginatedData<T> {
  total: number;
  limit: number;
  offset: number;
  rows: T[];
}
