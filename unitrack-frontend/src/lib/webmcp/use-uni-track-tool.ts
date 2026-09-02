/**
 * Adapter around `use-webmcp-tool`.
 *
 * Responsibilities:
 * - reuse the authenticated Axios client (`src/lib/api.ts`) inside `execute`;
 * - normalize every result into the UniTrack envelope and enforce the output
 *   budget;
 * - convert failures (including Axios errors) into JSON error envelopes that
 *   are surfaced as tool errors, never as successful empty output, and never
 *   leak Axios internals, stack traces, or HTML error pages;
 * - degrade to a no-op wherever `document.modelContext` is unavailable.
 */

import { useWebMCP } from "use-webmcp-tool";
import { isAxiosError } from "axios";
import {
  createEnvelope,
  fitToBudget,
  validateToolDefinition,
} from "./envelope";
import type { UniTrackEnvelope } from "./envelope";
import type {
  UniTrackToolAnnotations,
  UniTrackToolDefinition,
} from "./types";

export interface UniTrackRunResult {
  data: unknown;
  summary: string;
  scope?: Record<string, unknown>;
  warnings?: string[];
  counts?: Record<string, number>;
}

export type ToolStatusReporter = (
  tool: string,
  state:
    | "registered"
    | "unregistered"
    | "unsupported"
    | "registration-error"
    | "execution-error",
  detail?: string,
) => void;

/** Development-only status reporting: tool name/state only, no user data. */
export const reportToolStatus: ToolStatusReporter = (tool, state, detail) => {
  if (import.meta.env.DEV) {
    // eslint-disable-next-line no-console
    console.debug(`[webmcp] ${tool}: ${state}${detail ? ` (${detail})` : ""}`);
  }
};

/**
 * Extract a short, safe message from any failure. Never returns request
 * configs, stacks, or server HTML.
 */
export function safeFailureMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const statusCode = error.response?.status;
    const payload: unknown = error.response?.data;
    let detail = "Request failed";

    if (typeof payload === "string") {
      const trimmed = payload.trimStart();
      if (trimmed.length > 0 && trimmed.length < 300 && !trimmed.startsWith("<")) {
        detail = payload;
      }
    } else if (payload && typeof payload === "object") {
      const record = payload as Record<string, unknown>;
      const candidate = record.error ?? record.detail ?? record.message;
      if (typeof candidate === "string" && candidate.length < 300) {
        detail = candidate;
      }
    }

    return statusCode
      ? `Request failed (${statusCode}): ${detail}`
      : `Request failed: ${detail}`;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Unexpected error";
}

function errorEnvelope(tool: string, error: unknown): UniTrackEnvelope {
  return {
    tool,
    generated_at: new Date().toISOString(),
    scope: {},
    summary: safeFailureMessage(error),
    data: null,
    warnings: ["The tool call failed; no data was returned."],
  };
}

export interface UseUniTrackToolOptions<TArgs> {
  definition: UniTrackToolDefinition;
  run: (args: TArgs) => Promise<UniTrackRunResult>;
  /** Register only while true (e.g. after server-confirmed role agreement). */
  enabled?: boolean;
}

export function useUniTrackTool<TArgs>({
  definition,
  run,
  enabled = true,
}: UseUniTrackToolOptions<TArgs>) {
  const validation = validateToolDefinition(definition);
  const annotations: UniTrackToolAnnotations = {
    readOnlyHint: true,
    ...(definition.annotations ?? {}),
  };

  const { supported, registered, error } = useWebMCP({
    name: definition.name,
    description: definition.description,
    inputSchema: definition.inputSchema,
    annotations,
    enabled: enabled && validation.ok,
    execute: async (args: TArgs) => {
      try {
        const result = await run(args);
        return fitToBudget(
          createEnvelope({ tool: definition.name, result }),
        );
      } catch (executionError) {
        reportToolStatus(
          definition.name,
          "execution-error",
          safeFailureMessage(executionError),
        );
        // Thrown as JSON so the browser marks the result as an error while the
        // agent still receives a structured payload.
        throw new Error(
          JSON.stringify(errorEnvelope(definition.name, executionError)),
        );
      }
    },
    onError: (registrationError) => {
      reportToolStatus(
        definition.name,
        registrationError instanceof DOMException &&
          registrationError.name === "NotAllowedError"
          ? "registration-error"
          : "registration-error",
        registrationError instanceof Error
          ? registrationError.message
          : String(registrationError),
      );
    },
  });

  const state = !supported
    ? ("unsupported" as const)
    : registered
      ? ("registered" as const)
      : ("unregistered" as const);

  reportToolStatus(definition.name, state);

  return { supported, registered, error, definitionValid: validation.ok };
}