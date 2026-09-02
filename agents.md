# AGENTS.md — UniTrack WebMCP Integration

## Context

UniTrack is an existing final-year project management platform:
- **Backend:** Django REST Framework
- **Frontend:** React (Vite), deployed on Vercel
- **Roles:** Admin (departmental head — assigns supervisors, sets academic sessions), Supervisor (reviews/approves/rejects student chapter submissions), Student (submits chapters for review)

**Goal:** Add WebMCP tools to the existing frontend so an AI agent (ChatGPT's built-in browser, or Chrome with the WebMCP flag enabled) can call structured tools directly on a logged-in user's dashboard — without a separate backend integration. WebMCP runs entirely client-side: the page itself registers tools via the spec's API, and the agent calls them using the current user's existing session.

Read these before implementing anything:
- WebMCP spec/explainer: https://github.com/webmachinelearning/webmcp
- Chrome developer docs: https://developer.chrome.com/docs/ai/webmcp
- **Security guide (read this one carefully):** https://developer.chrome.com/docs/ai/webmcp/secure-tools

## Stack additions

- Use the `use-webmcp-tool` React hook (npm) to register tools cleanly inside existing dashboard components: https://www.npmjs.com/package/use-webmcp-tool
- Confirm the current spec API name before implementing (`document.modelContext.registerTool` — confirmed current as of the live spec at https://webmachinelearning.github.io/webmcp/).
- For local dev/testing across browsers (including non-Chromium ones), consider the `@mcp-b/webmcp-polyfill` package so tools are testable without chasing Canary-only flags.
- Tools should call the **existing DRF API endpoints** via `fetch()` wherever those endpoints already exist. Do not duplicate business logic client-side — the tool's `execute()` function is a thin wrapper around real API calls, using the same auth/session the logged-in user already has.

## Confirmed platform constraints (from official ChatGPT WebMCP docs — these are hard requirements, not preferences)

- **Top-level page only.** ChatGPT's built-in browser does NOT discover tools registered inside iframes — same-origin or cross-origin. Every `registerTool()` call must run in the top-level page's JS. Audit the React app first: if any dashboard content renders inside an `<iframe>`, tools registered there will silently never be discoverable. Move that logic to the top-level page if so.
- **Imperative API only.** The declarative form (HTML form `toolname`/`tooldescription` attributes) is NOT supported in ChatGPT's built-in browser — only `document.modelContext.registerTool()` works there. Don't bother implementing the declarative form for this submission.
- **Feature-detect before registering**, per the official pattern:
  ```js
  if (typeof document.modelContext?.registerTool === "function") {
    await document.modelContext.registerTool({ ... });
  }
  ```
  This also means the normal UI must keep working unmodified for browsers/users without WebMCP support — WebMCP is additive, never a replacement for existing UI paths.
- **Use `annotations: { readOnlyHint: true }`** on every tool that only reads data and never writes (e.g. `get_recurring_feedback_themes`, `find_stalled_students`, `compare_my_progress`, `explain_chapter_changes`). This is a real, supported field — it signals to the agent/browser that the tool is safe to call without extra confirmation, and reviewers may check for its correct use.
- Confirmed working setup for testing: **GPT-5.6 Terra** in the ChatGPT desktop app (GPT-5.6 Luna currently has WebMCP disabled — don't test with Luna).

## Tools to implement (priority order — build top to bottom; if time runs short, stop after whichever number and ship what's working over shipping all six half-done)

1. **`get_recurring_feedback_themes`** (Supervisor) — aggregates a supervisor's own feedback text across all their students this session, surfaces recurring issues (e.g. "citation formatting flagged in 6 of 8 submissions").
2. **`explain_chapter_changes`** (Supervisor) — compares two versions of a resubmitted chapter, narrates what changed and whether prior feedback points were addressed.
3. **`find_stalled_students`** (Admin + Supervisor) — cross-references submission timestamps + supervisor contact logs to flag students with no activity in 3+ weeks.
4. **`suggest_supervisor_assignment`** (Admin) — proposes a supervisor for an unassigned student based on current workload + expertise/topic match, with reasoning. Admin must still confirm — see security notes below.
5. **`generate_defense_questions`** (Student) — pulls a student's own chapter content + their supervisor's actual feedback history to generate targeted defense-prep questions.
6. **`compare_my_progress`** (Student) — anonymized cohort benchmarking (e.g. "% of cohort past chapter 3 by this week"). Must never expose another named student's data.

For each tool, define: `name`, `description`, `inputSchema` (JSON schema), `execute()`. Return structured JSON from `execute()` — not markdown or HTML — so the calling agent can format the response itself.

## Registration rules

- Only register a tool on the dashboard/component belonging to the role it's for — supervisor tools on the supervisor dashboard, admin tools on the admin dashboard, etc. Never register a tool where a user without that role's permissions could reach it.
- A tool must only ever return data the currently logged-in user already has permission to see via the existing DRF permission classes. Do not bypass or duplicate permission logic — call the real authenticated endpoints.

## Security / trust boundaries (this section is not optional — read the Chrome secure-tools guide first)

- Treat every tool's inputSchema and description as a potential prompt-injection surface. Assume a malicious page or malicious agent input could try to manipulate `execute()` into doing something the user didn't ask for.
- **No tool should silently commit a write with real consequences** (assigning a supervisor, approving/rejecting a submission) without a human-confirmed step in the actual UI. `suggest_supervisor_assignment` should *propose*, not *execute*, an assignment — route the actual write through the existing confirm-in-UI flow, not directly from the tool call.
- `compare_my_progress` must return aggregate/anonymized numbers only — never per-student breakdowns, names, or content.
- Do not expose destructive or bulk-write tools (mass reassignment, mass deletion) at all.

## Backend work (check existing models/endpoints before assuming new ones are needed)

Likely new DRF endpoints required:
- `/api/supervisor/feedback-history/` — full feedback text across a supervisor's students, for theme analysis
- `/api/submissions/<id>/versions/` — prior + current chapter version content, for diffing
- `/api/admin/stalled-students/` — submission timestamps + last supervisor contact, department-wide
- `/api/admin/supervisor-workload/` — supervisor capacity + expertise tags + student topic tags
- `/api/cohort-stats/` — anonymized aggregate submission-progress stats

Check existing models first — some of this data may already be stored and just needs a new serializer/view, not a migration.

## Testing

1. Install the **Model Context Tool Inspector** Chrome extension — lets you view registered tools on a page and invoke them manually without needing an LLM in the loop.
2. `chrome://flags/#enable-webmcp-testing` (Chrome Canary 146+ required — the flag is not present on stable/beta/dev channels) → Enabled → relaunch.
3. Open the deployed UniTrack URL, confirm tools appear correctly in the inspector with the right schema, test manual invocation per role.
4. Final test: open the deployed URL in **ChatGPT desktop app's built-in browser** (not chatgpt.com), logged in as each role, and ask natural-language questions that map to each tool.

## Submission deliverables (not code, but keep in mind while building — plan time for these)

- Live deployed URL (Vercel)
- Public GitHub repo with an OSS license file visible in the repo's "About" section
- <3 minute demo video with audio, showing what was built and how WebMCP is used
- Written description covering: why this use case fits WebMCP, how it improves the UX, what's newly possible that wasn't before, and a brief technical summary of the implementation