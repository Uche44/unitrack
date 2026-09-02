import { describe, expect, it } from "vitest";
import { suggestSupervisorAssignmentDefinition } from "./suggest-supervisor-assignment";

describe("suggest_supervisor_assignment definition", () => {
  it("requires a student id, bounds the limit, and is read-only", () => {
    expect(suggestSupervisorAssignmentDefinition.name).toBe("suggest_supervisor_assignment");
    expect(suggestSupervisorAssignmentDefinition.inputSchema).toEqual(
      expect.objectContaining({ additionalProperties: false }),
    );
    expect(suggestSupervisorAssignmentDefinition.inputSchema?.properties).toEqual(
      expect.objectContaining({
        student_id: expect.objectContaining({ type: "integer", minimum: 1 }),
        supervisor_id: expect.objectContaining({ type: "integer", minimum: 1 }),
        limit: expect.objectContaining({ type: "integer", minimum: 1, maximum: 10 }),
      }),
    );
    expect(suggestSupervisorAssignmentDefinition.inputSchema?.anyOf).toEqual([
      { required: ["student_id"] },
      { required: ["supervisor_id"] },
    ]);
    expect(suggestSupervisorAssignmentDefinition.annotations).toEqual({
      readOnlyHint: true,
    });
  });
});