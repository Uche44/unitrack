import { describe, expect, it } from "vitest";
import { findStalledStudentsDefinition } from "./find-stalled-students";

describe("find_stalled_students definition", () => {
  it("exposes a single threshold input with bounded range and untrusted annotation", () => {
    expect(findStalledStudentsDefinition.name).toBe("find_stalled_students");
    expect(findStalledStudentsDefinition.inputSchema).toEqual(
      expect.objectContaining({ additionalProperties: false }),
    );
    expect(findStalledStudentsDefinition.inputSchema?.properties).toEqual(
      expect.objectContaining({
        threshold_days: expect.objectContaining({
          type: "integer",
          minimum: 1,
          maximum: 90,
          default: 21,
        }),
      }),
    );
    expect(findStalledStudentsDefinition.annotations).toEqual({
      readOnlyHint: true,
      untrustedContentHint: true,
    });
  });
});