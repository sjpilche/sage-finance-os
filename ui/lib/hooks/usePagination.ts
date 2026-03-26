"use client";

import { useState, useCallback } from "react";

interface PaginationState {
  offset: number;
  limit: number;
}

export function usePagination(initialLimit = 100) {
  const [state, setState] = useState<PaginationState>({ offset: 0, limit: initialLimit });

  const nextPage = useCallback(() => {
    setState((s) => ({ ...s, offset: s.offset + s.limit }));
  }, []);

  const prevPage = useCallback(() => {
    setState((s) => ({ ...s, offset: Math.max(0, s.offset - s.limit) }));
  }, []);

  const goToPage = useCallback(
    (page: number) => {
      setState((s) => ({ ...s, offset: page * s.limit }));
    },
    []
  );

  const reset = useCallback(() => {
    setState((s) => ({ ...s, offset: 0 }));
  }, []);

  const page = Math.floor(state.offset / state.limit) + 1;

  return { ...state, page, nextPage, prevPage, goToPage, reset };
}
