import { useCallback, useState } from "react";
import api from "../api";
import type { UniTrackRunResult } from "./use-uni-track-tool";

interface ExplainArgs {
  submission_id: number;
  compare_to?: number;
}

interface DiffResponse {
  submission: Record<string, unknown>;
  comparison: Record<string, unknown> | null;
  diff: Record<string, unknown> | null;
  feedback_coverage: Array<Record<string, unknown>>;
  warnings: string[];
}

declare global {
  interface Window {
    modelContext?: {
      registerTool?: (tool: unknown, options?: { signal?: AbortSignal }) => unknown;
      callTool?: (
        name: string,
        args: Record<string, unknown>,
      ) => Promise<{ content: Array<{ type: string; text?: string }> }>;
    };
  }
  interface Document {
    modelContext?: Window["modelContext"];
  }
}

export function useExplainChapterChanges() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UniTrackRunResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const explain = useCallback(async (args: ExplainArgs) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (args.compare_to !== undefined) params.set("compare_to", String(args.compare_to));

      const request = api.get<DiffResponse>(
        `/api/submissions/${args.submission_id}/diff/${params.toString() ? `?${params}` : ""}`,
      );

      const response = await request;
      const data = response.data;

      setResult({
        data,
        summary: data.comparison
          ? `Compared submission ${data.submission.id} against version ${(data.comparison as { version?: number }).version}.`
          : `Submission ${data.submission.id} is the first version; no previous submission to compare.`,
        scope: {
          submission_id: data.submission.id,
          comparison_id: data.comparison?.id ?? null,
        },
        warnings: data.warnings,
        counts: {
          coverage_items: data.feedback_coverage.length,
          added_paragraphs: (data.diff?.added_paragraph_total as number | undefined) ?? 0,
          removed_paragraphs: (data.diff?.removed_paragraph_total as number | undefined) ?? 0,
        },
      });
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Unable to load diff";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { explain, loading, result, error };
}