import { describe, expect, it } from "vitest";
import { generateDefenseQuestionsDefinition } from "./generate-defense-questions";

describe("generate_defense_questions definition", () => {
  it("uses bounded filters and read-only/untrusted annotations", () => {
    expect(generateDefenseQuestionsDefinition.name).toBe("generate_defense_questions");
    expect(generateDefenseQuestionsDefinition.inputSchema).toEqual(
      expect.objectContaining({ additionalProperties: false }),
    );
    expect(generateDefenseQuestionsDefinition.inputSchema?.properties).toEqual(
      expect.objectContaining({
        milestone: expect.objectContaining({
          enum: ["proposal", "chapter_one", "chapter_two", "final_report"],
        }),
        difficulty: expect.objectContaining({
          enum: ["easy", "medium", "hard"],
        }),
        limit: expect.objectContaining({ type: "integer", minimum: 1, maximum: 25 }),
      }),
    );
    expect(generateDefenseQuestionsDefinition.annotations).toEqual({
      readOnlyHint: true,
      untrustedContentHint: true,
    });
  });
});