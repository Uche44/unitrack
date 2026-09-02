import { describe, expect, it } from "vitest";
import { compareMyProgressDefinition } from "./compare-my-progress";

describe("compare_my_progress definition", () => {
  it("accepts no inputs, is read-only, and exposes no peer identifiers", () => {
    expect(compareMyProgressDefinition.name).toBe("compare_my_progress");
    expect(compareMyProgressDefinition.inputSchema).toEqual(
      expect.objectContaining({ additionalProperties: false }),
    );
    expect(compareMyProgressDefinition.inputSchema?.properties ?? {}).toEqual({});
    expect(compareMyProgressDefinition.annotations).toEqual({
      readOnlyHint: true,
    });
  });
});