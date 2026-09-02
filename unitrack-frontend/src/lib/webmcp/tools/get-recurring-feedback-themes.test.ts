import { describe, expect, it } from "vitest";
import { recurringFeedbackThemeDefinition } from "./get-recurring-feedback-themes";

describe("get_recurring_feedback_themes definition", () => {
  it("uses strict bounded inputs and marks feedback as untrusted", () => {
    expect(recurringFeedbackThemeDefinition.name).toBe("get_recurring_feedback_themes");
    expect(recurringFeedbackThemeDefinition.inputSchema).toEqual(
      expect.objectContaining({ additionalProperties: false }),
    );
    expect(recurringFeedbackThemeDefinition.inputSchema?.properties).toEqual(
      expect.objectContaining({
        session_id: expect.objectContaining({ type: "integer", minimum: 1 }),
        min_occurrences: expect.objectContaining({ minimum: 1, maximum: 100 }),
        limit: expect.objectContaining({ minimum: 1, maximum: 7 }),
      }),
    );
    expect(recurringFeedbackThemeDefinition.annotations).toEqual({
      readOnlyHint: true,
      untrustedContentHint: true,
    });
  });
});
