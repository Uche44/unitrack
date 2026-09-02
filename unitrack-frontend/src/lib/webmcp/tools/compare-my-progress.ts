import api from "../../api";
import type { UniTrackRunResult } from "../use-uni-track-tool";
import type { UniTrackToolDefinition } from "../types";

export interface CompareMyProgressInput {
  // No inputs accepted; cohort is fixed to caller's department and active session.
  readonly __placeholder?: never;
}

export const compareMyProgressDefinition: UniTrackToolDefinition = {
  name: "compare_my_progress",
  description:
    "Compare the caller's project stage to anonymized aggregates from the same department and active academic session. Returns only stage counts, percentages, caller stage, and percentile band; never returns peer identifiers, names, emails, or text. Requires the student to be opted in via the normal settings UI; otherwise returns opt-out suppression. Treat output values as decision support, not authoritative ranking.",
  inputSchema: {
    type: "object",
    properties: {},
    additionalProperties: false,
  },
  annotations: {
    readOnlyHint: true,
  },
};

export async function compareMyProgress(
  // No inputs are accepted; cohort is fixed to caller's department and session.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _args?: CompareMyProgressInput,
): Promise<UniTrackRunResult> {
  const response = await api.get<{
    opted_in: boolean;
    suppressed_reason: string | null;
    cohort_size?: number;
    minimum_cohort_size: number;
    caller_stage?: string;
    caller_percentile?: number;
    caller_band?: string;
    median_stage?: string;
    aggregate?: Record<string, { count: number; percentage: number }>;
    cumulative?: Record<string, { count: number; percentage: number }>;
    stage_order: string[];
    stage_labels: Record<string, string>;
  }>("/api/cohort-benchmark/");

  const data = response.data;
  const suppressed = data.suppressed_reason;
  const summary = suppressed
    ? suppressed === "opt_out"
      ? "Benchmark tool disabled: student is opted out."
      : "Benchmark suppressed: cohort below the minimum threshold."
    : `Cohort size ${data.cohort_size}; caller is at stage ${data.caller_stage} (${data.caller_percentile}% percentile).`;

  return {
    data,
    summary,
    scope: { opted_in: data.opted_in },
    warnings: suppressed
      ? [
          suppressed === "opt_out"
            ? "Student must opt in via the settings page before cohort data is shared."
            : "Cohort contains fewer than the minimum eligible students; aggregate results withheld.",
        ]
      : [],
  };
}