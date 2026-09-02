import { describe, expect, it } from "vitest";
import { explainChapterChangesDefinition } from "./explain-chapter-changes";

describe("explain_chapter_changes definition", () => {
  it("uses strict integer IDs and untrusted annotations", () => {
    expect(explainChapterChangesDefinition.name).toBe("explain_chapter_changes");
    expect(explainChapterChangesDefinition.inputSchema).toEqual(
      expect.objectContaining({ additionalProperties: false }),
    );
    expect(explainChapterChangesDefinition.inputSchema?.properties).toEqual(
      expect.objectContaining({
        submission_id: expect.objectContaining({ type: "integer", minimum: 1 }),
        compare_to: expect.objectContaining({ type: "integer", minimum: 1 }),
        detail: expect.objectContaining({
          enum: ["concise", "detailed"],
        }),
      }),
    );
    expect(explainChapterChangesDefinition.inputSchema?.required).toEqual([
      "submission_id",
    ]);
    expect(explainChapterChangesDefinition.annotations).toEqual({
      readOnlyHint: true,
      untrustedContentHint: true,
    });
  });
});