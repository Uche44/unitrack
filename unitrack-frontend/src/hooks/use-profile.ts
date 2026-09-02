import { useCallback, useEffect, useState } from "react";
import api from "../lib/api";

export function useProfile() {
  const [areasOfExpertise, setAreasOfExpertise] = useState("");
  const [projectInterests, setProjectInterests] = useState("");
  const [savingField, setSavingField] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .get<{ areas_of_expertise: string; project_interests: string }>(
        "/api/profile/",
      )
      .then((response) => {
        if (cancelled) return;
        setAreasOfExpertise(response.data.areas_of_expertise ?? "");
        setProjectInterests(response.data.project_interests ?? "");
      })
      .catch((caught) => {
        if (cancelled) return;
        setError(
          caught instanceof Error ? caught.message : "Failed to load profile",
        );
      })
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const save = useCallback(
    async (
      field: "areas_of_expertise" | "project_interests",
      value: string,
    ) => {
      setSavingField(field);
      setError(null);
      try {
        await api.put("/api/profile/", { [field]: value });
      } catch (caught) {
        const message =
          caught instanceof Error ? caught.message : "Failed to save profile";
        setError(message);
        throw caught;
      } finally {
        setSavingField(null);
      }
    },
    [],
  );

  return {
    areasOfExpertise,
    setAreasOfExpertise,
    projectInterests,
    setProjectInterests,
    savingField,
    error,
    loaded,
    save,
  };
}