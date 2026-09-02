import { useCallback, useEffect, useState } from "react";
import api from "../api";

export function useBenchmarkPreference() {
  const [optedIn, setOptedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get<{ benchmark_opt_in: boolean }>(
        "/api/benchmark-preference/",
      );
      setOptedIn(Boolean(response.data.benchmark_opt_in));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load preference");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const setPreference = useCallback(
    async (nextValue: boolean) => {
      const previous = optedIn;
      setOptedIn(nextValue);
      try {
        await api.put("/api/benchmark-preference/", {
          benchmark_opt_in: nextValue,
        });
      } catch (caught) {
        setOptedIn(previous);
        setError(
          caught instanceof Error ? caught.message : "Failed to save preference",
        );
        throw caught;
      }
    },
    [optedIn],
  );

  return { optedIn, loading, error, refresh, setPreference };
}