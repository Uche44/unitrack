import api from "../../api";
import type { UniTrackRunResult } from "../use-uni-track-tool";
import type { UniTrackToolDefinition } from "../types";

export interface SuggestSupervisorAssignmentInput {
  student_id?: number;
  supervisor_id?: number;
  limit?: number;
}

export const suggestSupervisorAssignmentDefinition: UniTrackToolDefinition = {
  name: "suggest_supervisor_assignment",
  description:
    "Read-only ranking tool for the admin's assignment flow. Supply supervisor_id to find unassigned students whose project_interests match that supervisor's areas_of_expertise. Supply student_id to find supervisors for a given student. Returns scored candidates with matched keywords, load/capacity, and plain-language reasoning. The tool does not assign; an admin must confirm in the existing UI.",
  inputSchema: {
    type: "object",
    properties: {
      student_id: { type: "integer", minimum: 1 },
      supervisor_id: { type: "integer", minimum: 1 },
      limit: { type: "integer", minimum: 1, maximum: 10, default: 5 },
    },
    additionalProperties: false,
    anyOf: [
      { required: ["student_id"] },
      { required: ["supervisor_id"] },
    ],
  },
  annotations: {
    readOnlyHint: true,
  },
};

export async function suggestSupervisorAssignment(
  args: SuggestSupervisorAssignmentInput,
): Promise<UniTrackRunResult> {
  const params = new URLSearchParams();
  if (args.limit !== undefined) params.set("limit", String(args.limit));
  if (args.supervisor_id !== undefined) {
    params.set("supervisor_id", String(args.supervisor_id));
  }
  if (args.student_id !== undefined) {
    params.set("student_id", String(args.student_id));
  }

  const response = await api.get<{
    mode?: string;
    student?: Record<string, unknown>;
    supervisor?: Record<string, unknown>;
    session: number | null;
    candidates: Array<Record<string, unknown>>;
    excluded?: Array<Record<string, unknown>>;
    result: string;
  }>(
    `/api/suggest-supervisor/${params.toString() ? `?${params}` : ""}`,
  );

  const candidates = response.data.candidates;
  const top = candidates[0];
  const isStudentMode = response.data.mode === "supervisor_for_student";
  const summary =
    response.data.result === "no_suitable_supervisor" ||
    response.data.result === "no_suitable_students"
      ? "No suitable matches found for the supplied identifier."
      : isStudentMode
        ? `Top supervisor: ${top?.full_name ?? "n/a"} (score ${top?.total_score ?? "n/a"}).`
        : `Top student: ${top?.full_name ?? "n/a"} (score ${top?.expertise_score ?? "n/a"}).`;

  return {
    data: response.data,
    summary,
    scope: {
      mode: response.data.mode,
      student_id: args.student_id,
      supervisor_id: args.supervisor_id,
    },
    counts: {
      candidates: candidates.length,
      excluded: response.data.excluded?.length ?? 0,
    },
  };
}