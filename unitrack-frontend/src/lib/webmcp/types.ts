/**
 * WebMCP platform types for UniTrack.
 *
 * The `use-webmcp-tool` package ships its own tool-definition types. The only
 * thing it does not provide is a typed surface for the raw imperative
 * `document.modelContext` API, so that is declared narrowly here (module-local
 * type, no global augmentation) and used only by the adapter.
 */

export interface UniTrackToolAnnotations {
  /** All UniTrack tools are read-only. */
  readOnlyHint?: boolean;
  /** True when output contains user-authored text (feedback, notes, documents). */
  untrustedContentHint?: boolean;
}

export interface UniTrackToolDefinition {
  /** Stable tool identifier. Max 30 characters (see WEBMCP_LIMITS). */
  name: string;
  /** Natural-language description for the calling agent. Max 500 characters. */
  description: string;
  /** JSON Schema describing the tool arguments. */
  inputSchema?: Record<string, unknown>;
  annotations?: UniTrackToolAnnotations;
}

/** Raw imperative WebMCP API (https://github.com/webmachinelearning/webmcp). */
export interface RawModelContext {
  registerTool(
    tool: {
      name: string;
      description: string;
      inputSchema?: Record<string, unknown>;
      annotations?: UniTrackToolAnnotations;
      execute: (args: never) => unknown;
    },
    options?: { signal?: AbortSignal },
  ): unknown;
}

/** Status reported by tool hosts (development only). */
export type WebMCPToolState =
  | "registered"
  | "unregistered"
  | "unsupported"
  | "registration-error"
  | "execution-error";