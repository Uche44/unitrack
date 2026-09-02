/**
 * Standard UniTrack WebMCP result envelope and output budgets.
 *
 * Every tool returns this shape so the calling agent always receives bounded,
 * structured JSON (never HTML, never Axios internals).
 */

export const WEBMCP_LIMITS = {
  /** Tool and parameter names. */
  MAX_NAME_CHARS: 30,
  /** Tool description budget. */
  MAX_DESCRIPTION_CHARS: 500,
  /** Parameter description budget. */
  MAX_PARAM_DESCRIPTION_CHARS: 150,
  /** Serialized tool output budget. */
  MAX_OUTPUT_CHARS: 1500,
  /** Maximum number of items returned in `data`. */
  MAX_ITEMS: 25,
} as const;

export interface UniTrackEnvelope {
  tool: string;
  generated_at: string;
  scope: Record<string, unknown>;
  summary: string;
  data: unknown;
  warnings: string[];
  counts?: Record<string, number>;
}

export interface UniTrackRunResult {
  data: unknown;
  summary: string;
  scope?: Record<string, unknown>;
  warnings?: string[];
  counts?: Record<string, number>;
}

export function createEnvelope(input: {
  tool: string;
  result: UniTrackRunResult;
  extraWarnings?: string[];
}): UniTrackEnvelope {
  return {
    tool: input.tool,
    generated_at: new Date().toISOString(),
    scope: input.result.scope ?? {},
    summary: input.result.summary,
    data: input.result.data,
    warnings: [...(input.result.warnings ?? []), ...(input.extraWarnings ?? [])],
    counts: input.result.counts,
  };
}

/** Bound a result list and report truncation. */
export function limitItems<T>(
  items: T[],
  max: number = WEBMCP_LIMITS.MAX_ITEMS,
): { items: T[]; total: number; truncated: boolean } {
  const total = items.length;
  if (total <= max) {
    return { items, total, truncated: false };
  }
  return { items: items.slice(0, max), total, truncated: true };
}

function findArrayKeys(value: unknown): string[] {
  if (!value || typeof value !== "object") return [];
  return Object.entries(value as Record<string, unknown>)
    .filter(([, v]) => Array.isArray(v))
    .map(([k]) => k);
}

/**
 * Shrink an envelope until its serialized form fits the output budget.
 * Array-valued fields are trimmed first; a warning records the truncation.
 */
export function fitToBudget(
  envelope: UniTrackEnvelope,
  budget: number = WEBMCP_LIMITS.MAX_OUTPUT_CHARS,
): UniTrackEnvelope {
  const warn = (): UniTrackEnvelope => ({
    ...envelope,
    warnings: [
      ...envelope.warnings,
      "Output truncated to fit the tool response budget.",
    ],
  });

  if (JSON.stringify(envelope).length <= budget) {
    return envelope;
  }

  let current = envelope;
  let guard = 0;
  while (JSON.stringify(current).length > budget && guard < 12) {
    const keys = findArrayKeys(current.data);
    if (keys.length === 0) break;
    const nextData: Record<string, unknown> = {
      ...(current.data as Record<string, unknown>),
    };
    for (const key of keys) {
      const arr = nextData[key] as unknown[];
      if (arr.length > 1) {
        nextData[key] = arr.slice(0, Math.max(1, Math.floor(arr.length / 2)));
      } else {
        nextData[key] = [];
      }
    }
    current = { ...current, data: nextData };
    guard += 1;
  }

  if (JSON.stringify(current).length > budget) {
    current = {
      ...current,
      data: null,
      summary: current.summary.slice(0, 300),
    };
  }
  return warn();
}

/** Validate a tool definition against the published naming budgets. */
import type { UniTrackToolDefinition } from "./types";

export function validateToolDefinition(
  definition: UniTrackToolDefinition,
): { ok: true } | { ok: false; reason: string } {
  if (
    !definition.name ||
    definition.name.length > WEBMCP_LIMITS.MAX_NAME_CHARS
  ) {
    return {
      ok: false,
      reason: `Tool name must be 1-${WEBMCP_LIMITS.MAX_NAME_CHARS} characters.`,
    };
  }
  if (
    !definition.description ||
    definition.description.length > WEBMCP_LIMITS.MAX_DESCRIPTION_CHARS
  ) {
    return {
      ok: false,
      reason: `Tool description must be 1-${WEBMCP_LIMITS.MAX_DESCRIPTION_CHARS} characters.`,
    };
  }
  return { ok: true };
}