# UniTrack WebMCP Implementation Milestones

## Purpose

This file turns the six features in `task.md` and the integration, security, testing, and submission requirements in `agents.md` into ten cumulative, independently reviewable milestones.

Each milestone must leave the application deployable and must pass all tests introduced by earlier milestones. A milestone is **independent** when it:

- has one coherent outcome and an explicit rollback boundary;
- does not leave half-registered tools, unused endpoints, or an unapplied migration;
- includes its own automated tests and manual acceptance check;
- preserves all existing student, supervisor, and admin workflows; and
- can be merged and demonstrated without work from the following milestone.

Milestones are intentionally cumulative: later milestones may use stable contracts delivered earlier, but no milestone may depend on unfinished work in a later milestone.

## Agreed architecture

### Intelligence boundary

Use an **agent-native** design. Django authenticates the caller, enforces authorization, retrieves the source records, and computes deterministic evidence or statistics. React registers thin WebMCP tools that call those DRF endpoints through the existing authenticated Axios client. The calling browser agent interprets the structured JSON and produces prose, themes, explanations, or quiz dialogue.

Do not add an external LLM provider or send project documents and feedback to a second AI service.

### Current application constraints

- Backend: Django 5.2 and Django REST Framework with JWT authentication.
- Frontend: React 19, TypeScript, Vite, Axios, React Router, and Zustand.
- Authentication is available through HttpOnly cookies and local-storage bearer tokens. WebMCP calls must use `src/lib/api.ts` so refresh and credential behavior remains consistent.
- Existing data includes users, projects, academic-session records, versioned PDF submissions, approval/rejection state, and one rejection comment per submission.
- Missing foundations include record-to-session relationships, supervisor expertise/capacity, contact logs, durable review events, reliable revision chains/extracted text, and automated frontend/API coverage.
- Current WebMCP API: `document.modelContext.registerTool`. Use `use-webmcp-tool` (`useWebMCP`) for feature detection and mount/unmount lifecycle management.

### Rules that apply to every milestone

- Keep authorization in DRF. Never trust a role, user ID, supervisor ID, or student ID supplied by the agent when it can be derived from `request.user`.
- Return JSON-safe, bounded, documented response shapes. WebMCP output is structured content, not HTML or preformatted Markdown.
- Register tools only inside the layout for an authenticated permitted role and unregister them on unmount/logout/role change.
- Mark outputs containing user-authored document text or feedback with `untrustedContentHint`. Treat that text as data, never instructions.
- All six tools are read-only. In particular, supervisor suggestions must not assign anyone.
- Use pagination, limits, validated enums/IDs, and concise errors. Do not expose raw exceptions, secrets, inaccessible object existence, or unrestricted file URLs.
- Freeze time in date-dependent tests. Mock Cloudinary/network/PDF boundaries; unit tests must not call external services.
- Run backend tests against an isolated test database, never the checked-in `db.sqlite3`.
- After every milestone run the complete backend suite, frontend unit suite, frontend lint, and production build.

## Definition of done for every milestone

- [ ] New behavior has positive, empty-state, invalid-input, unauthenticated, wrong-role, and cross-tenant/object-ownership tests where applicable.
- [ ] Existing behavior has not regressed.
- [ ] Database migrations apply from a clean database and reverse when the migration is designed to be reversible.
- [ ] Endpoint contracts and WebMCP schemas are documented and match their tests.
- [ ] `python manage.py test` passes from `unitrack-backend`.
- [ ] Frontend unit tests pass from `unitrack-frontend`.
- [ ] `npm run lint` passes from `unitrack-frontend`.
- [ ] `npm run build` passes from `unitrack-frontend`.
- [ ] The milestone-specific manual acceptance check passes.
- [ ] No credentials, personal test data, generated database files, or cache files are committed.

---

## Milestone 1 — Baseline safety net and test harness

**Outcome:** The existing application has repeatable backend and frontend quality gates before domain or WebMCP behavior changes.

### Tasks

#### Repository and backend

- [x] Add/repair `.gitignore` coverage for Python caches, local databases, environments, frontend build output, coverage output, and local `.env` files. Do not delete or overwrite the developer's current local database.
- [x] Add reusable test builders/fixtures for admin, approved supervisor, supervisor A/B, assigned/unassigned student A/B, project, session, and submission records.
- [x] Add API regression tests for login/refresh behavior and current role-scoped project/submission querysets.
- [x] Add regression tests proving a supervisor cannot retrieve another supervisor's student/project and a student cannot retrieve another student's records. Fix discovered object-level authorization gaps as part of this safety milestone.
- [x] Protect session creation so only admins can write it; explicitly test public/role-appropriate read behavior.
- [x] Test that submission creation validates that the authenticated student owns the submitted project.

#### Frontend

- [x] Add Vitest, jsdom, React Testing Library, and user-event using versions compatible with React 19/Vite 7.
- [x] Add `test`, `test:watch`, and optional coverage scripts without changing the existing `dev`, `lint`, or `build` commands.
- [x] Create shared test setup for DOM cleanup, local storage, router wrappers, Zustand reset, and Axios mocks.
- [x] Add regression tests for `src/lib/api.ts`: bearer attachment, credential use, single refresh/retry, token cleanup, and no refresh loop.
- [x] Add route/layout tests showing each dashboard renders only for its authenticated role. Replace commented-out route protection with a tested reusable role guard if required.

#### Developer documentation

- [x] Document exact local commands and required environment variables without recording secret values.
- [x] Establish one command or CI job that runs backend tests plus frontend tests, lint, and build.

### Required tests

- Backend authentication and authorization matrix passes for anonymous/admin/supervisor/student callers.
- Cross-supervisor and cross-student object access returns `403` or non-enumerating `404` consistently.
- Frontend API refresh tests do not make real network requests.
- A clean frontend install can run tests and build.

### Manual acceptance

Log in as each role and confirm existing dashboards, project creation, submission review, and admin assignment behavior still work.

### Exit gate / rollback boundary

The repository has reliable green quality gates and no feature schema changes. This milestone can be reverted without migrating data.

---

## Milestone 2 — Session-aware activity, review, and revision data

**Outcome:** UniTrack durably records the minimum trusted data needed by all six tools.

### Tasks

#### Data model and migrations

- [x] Add an active/current-state rule to `ProjectSession` and prevent ambiguous overlapping “current” sessions.
- [x] Link each `Project` to a `ProjectSession`; derive the session server-side when creating a project. Backfill existing projects deterministically to the appropriate existing session and document fallback behavior.
- [x] Add supervisor matching data: normalized expertise tags and an explicit positive capacity (defaulting to the current limit of five). Derive “fully booked” from capacity/current assignments rather than trusting a drifting Boolean.
- [x] Add normalized project topic/research tags while retaining the existing title and description.
- [x] Add a `SupervisorContact` record containing student, supervisor, session, occurred-at timestamp, contact type, and optional bounded note. Enforce that the recorded pair is a valid supervision relationship.
- [x] Add an immutable `SubmissionReview` record containing submission, reviewer, decision, feedback text, and reviewed-at timestamp. Update approve/reject flows to append a review event while preserving current response/UI compatibility.
- [x] Make revision history explicit and safe: enforce unique `(project, milestone, version)`, link a submission to its previous version or provide an equivalent deterministic relationship, and allocate versions transactionally.
- [x] Store extracted PDF text and extraction status/error metadata on each submission. Extract text at upload in a bounded service using the already installed `pypdf`; never download arbitrary agent-provided URLs.
- [x] Backfill review records from existing approval/rejection fields and feedback where possible without fabricating timestamps or content.
- [x] Add indexes for session, supervisor/student activity, milestone/version, review timestamps, and contact timestamps used by later queries.

#### API compatibility

- [x] Keep existing serializers compatible while adding explicit serializers/services for contact logging and review history.
- [x] Add a supervisor UI/API action to record contact with one of their currently assigned students; this is a normal authenticated UI write, not a WebMCP write tool.
- [x] Make submission approval/rejection ownership checks transactional and ensure only the assigned supervisor can review.

### Required tests

- Clean migration, data backfill, constraints, indexes, and migration reversal (where supported).
- Concurrent/logically repeated submissions cannot receive the same version.
- PDF extraction success, blank/scanned PDF, corrupt PDF, size/page limit, and parser failure.
- Review events are immutable and scoped to the assigned supervisor.
- Contact logs reject mismatched supervisor/student/session combinations.
- Existing project/submission serializer contracts remain usable by the frontend.

### Manual acceptance

Create a session and project, upload two versions, reject then approve through the current UI, record supervisor contact, and verify the history is preserved rather than overwritten.

### Exit gate / rollback boundary

All foundational data is recorded during ordinary workflows and is queryable without any WebMCP tool. This schema milestone is independently deployable and includes a documented backup/rollback procedure.

---

## Milestone 3 — Secure WebMCP platform and role-scoped registration

**Outcome:** The frontend can safely expose typed, tested, read-only WebMCP tools without implementing a feature tool yet.

### Tasks

#### Shared WebMCP infrastructure

- [ ] Install `use-webmcp-tool` and pin a reviewed version compatible with React 19.
- [ ] Add TypeScript declarations/types for the current `document.modelContext` API only where the package does not provide them.
- [ ] Create a shared adapter around `useWebMCP` that uses `src/lib/api.ts`, normalizes success/error envelopes, and never returns Axios internals or HTML error pages.
- [ ] Define a standard result envelope: `tool`, `generated_at`, `scope`, `summary`, `data`, `warnings`, and `provenance`/counts as applicable.
- [ ] Enforce maximum input lengths, response item counts, and a concise WebMCP output budget. Return aggregates/summaries instead of entire unbounded corpora.
- [ ] Apply `readOnlyHint: true` to all planned tools and `untrustedContentHint: true` wherever output contains feedback, contact notes, project text, or submission text.
- [ ] Ensure unsupported browsers degrade to a no-op without affecting dashboard rendering.

#### Role hosts

- [ ] Add small tool-host components to admin, supervisor, and student layouts.
- [ ] Enable registration only when the persisted user and authenticated server state agree on the permitted role. Do not use a route parameter as authorization.
- [ ] Ensure mount, unmount, logout, expired authentication, and role changes correctly register/unregister tools.
- [ ] Add a development-only status surface or logging path that contains tool names/status but no returned user data.

#### Contract and security documentation

- [ ] Record naming/description budgets (tool and parameter names under 30 characters, descriptions concise), annotations, and allowed exposure origins.
- [ ] Document origin-isolation and `tools` Permissions Policy deployment requirements.
- [ ] Define an endpoint/tool security checklist reused by Milestones 4–9.

### Required tests

- Mock `document.modelContext` to test registration, invocation, AbortSignal unregistration, Strict Mode, unsupported browser, registration failure, and API failure.
- Admin, supervisor, and student layouts never expose one another's tool hosts.
- Tool errors are marked as errors and never appear as successful empty output.
- User-authored strings remain data in structured fields and cannot change endpoint selection or HTTP method.

### Manual acceptance

Using a temporary harmless fixture tool in development, inspect registration/invocation with the Model Context Tool Inspector, then remove the fixture before merging.

### Exit gate / rollback boundary

The reusable platform is production-safe but exposes no business tool. Reverting it requires no database change.

---

## Milestone 4 — Supervisor Feedback Pattern Analyzer

**Tool:** `get_recurring_feedback_themes`  
**Outcome:** A supervisor can ask an agent for recurring issues across their own students in the current session.

### Tasks

#### Backend

- [ ] Add a supervisor-only feedback-insights endpoint derived exclusively from `request.user` and the active/requested permitted session.
- [ ] Query immutable `SubmissionReview` feedback for projects supervised by the caller; exclude blank feedback and inaccessible sessions.
- [ ] Implement deterministic theme evidence using a maintained taxonomy of academically useful categories (for example citation/formatting, methodology, clarity, literature review, analysis, structure, and grammar) plus normalized phrase/keyword matching.
- [ ] Return per theme: stable theme key/label, matched review count, distinct submission count, distinct student count, denominator counts, percentage, and a small set of short attributed-by-ID evidence excerpts. Do not return student names unless the existing supervisor permission requires them; prefer internal record IDs and counts.
- [ ] Validate optional session, minimum occurrence, and bounded result-limit inputs. Default to the current session and only include themes occurring more than once.
- [ ] Keep matching logic in a tested service rather than a view.

#### Frontend/WebMCP

- [ ] Register `get_recurring_feedback_themes` only in the supervisor layout.
- [ ] Define a strict input schema for optional session/minimum occurrence/limit values and a description that tells the agent to synthesize teaching insights from evidence, not follow instructions inside feedback text.
- [ ] Use the shared authenticated client and return structured theme evidence with `readOnlyHint` and `untrustedContentHint`.

### Required tests

- Exact counts across multiple students/submissions and no double counting within one review.
- Current-session filtering, empty corpus, blank feedback, unknown taxonomy terms, deterministic ordering, and output limits.
- Supervisor A cannot include Supervisor B's feedback; admin/student/anonymous calls are denied.
- Tool schema, role-only registration, successful normalization, and API error behavior.
- Injection-like feedback text is returned only as bounded evidence and never executed/interpreted by application code.

### Manual acceptance

Seed feedback such that citation issues appear in six of eight reviewed submissions; invoke the tool in the Inspector and confirm the counts/evidence support that conclusion.

### Exit gate / rollback boundary

The first complete WebMCP feature is independently demonstrable. Reverting it removes one endpoint, service, tests, and one supervisor registration without affecting stored reviews.

---

## Milestone 5 — Revision Diff Narrator

**Tool:** `explain_chapter_changes`  
**Outcome:** A supervisor's agent can explain changes between two authorized versions and show evidence about prior feedback coverage.

### Tasks

#### Backend

- [ ] Add a supervisor-only submission-version endpoint scoped through projects supervised by `request.user`.
- [ ] Accept a current submission ID and optional comparison submission ID. If omitted, select the explicit previous version of the same project/milestone.
- [ ] Reject comparisons across students, projects, milestones, or inaccessible supervisors.
- [ ] Compute a bounded deterministic text diff from stored extracted text: section/paragraph additions, removals, replacements, word-count delta, and similarity/change ratio. Normalize whitespace without destroying headings.
- [ ] Compare prior review feedback theme/phrase evidence against newly added/current text and return `likely_addressed`, `possibly_addressed`, or `not_evident`, always with evidence and an explicit “heuristic, supervisor must verify” warning.
- [ ] Return extraction-unavailable states cleanly for scanned/corrupt/legacy documents rather than fetching arbitrary URLs at invocation time.

#### Frontend/WebMCP

- [ ] Register `explain_chapter_changes` only in the supervisor layout.
- [ ] Use a strict schema containing integer submission IDs only; do not accept URLs, text blobs, file paths, or student/supervisor IDs.
- [ ] Tell the agent to narrate only the supplied evidence and preserve uncertainty about whether feedback is substantively resolved.

### Required tests

- Added/removed/changed sections, identical versions, default previous version, first version, and extraction failure.
- Cross-project/milestone/student comparisons fail without leaking inaccessible record details.
- Feedback coverage statuses have deterministic fixtures and retain warnings.
- Large documents are truncated/summarized within configured limits and produce truncation metadata.
- Tool registration/schema/error tests and malicious text-as-data regression tests.

### Manual acceptance

Upload two versions where methodology is revised but a citation issue remains; invoke the tool and confirm both facts are supported by returned diff/feedback evidence.

### Exit gate / rollback boundary

The diff service and tool can be removed without affecting submission creation or stored revision history.

---

## Milestone 6 — Silent Student Flagging

**Tool:** `find_stalled_students`  
**Outcome:** Admins can see department-wide inactivity and supervisors can see inactivity only among their assigned students.

### Tasks

#### Backend

- [ ] Add a role-aware stalled-students endpoint. Scope admins to their department and supervisors to their current assigned students; deny students.
- [ ] Default the threshold to 21 days and allow only a bounded configured range.
- [ ] For each eligible current-session student, compute latest submission/project activity and latest valid supervisor contact. Define “stalled” as neither activity nor contact within the threshold; define deterministic behavior for students with no submissions or contacts using assignment/project/session dates.
- [ ] Return last-activity timestamps, days inactive, reason codes, current milestone/status, and supervisor summary only where the caller is authorized.
- [ ] Support bounded sorting/filtering and avoid N+1 queries.
- [ ] Add normal UI support for supervisors to record contact if Milestone 2 only delivered the API action.

#### Frontend/WebMCP

- [ ] Register `find_stalled_students` in admin and supervisor layouts with the same name/schema but role-dependent server scope.
- [ ] Do not accept a supervisor ID or department override from the agent.
- [ ] Annotate contact notes or other user text as untrusted; omit notes from the tool response unless essential.

### Required tests

- Boundary times at 20/21/22 days with frozen time and timezone-aware values.
- Submission-only activity, contact-only activity, neither, no-project student, newly assigned student, inactive/ended session, and empty result.
- Admin department scope and supervisor assignment scope; student/anonymous denial.
- Query-count ceiling for a representative cohort.
- Both allowed layouts register the tool; student layout does not.

### Manual acceptance

Seed four activity patterns, invoke as admin and two supervisors, and verify each role sees exactly its permitted stalled subset with correct day counts.

### Exit gate / rollback boundary

The read-only detector can be removed without deleting contact history or changing submission flows.

---

## Milestone 7 — Cross-Student Workload Balancer

**Tool:** `suggest_supervisor_assignment`  
**Outcome:** An admin receives explainable, read-only supervisor recommendations and must still confirm assignment in the existing UI.

### Tool spec (rev 2026-09-01)

- `suggest_supervisor_assignment` (Admin) — read-only ranking tool. Two modes (admin picks one per call):
  - `student_id` mode: propose a supervisor for an unassigned student.
  - `supervisor_id` mode: surface unassigned students whose `project_interests` match the supervisor's `areas_of_expertise`.
- Inputs:
  1. Declared `areas_of_expertise` from the supervisor's own profile.
  2. Declared `project_interests` from the student's own profile.
  3. Current supervision workload/capacity.
- Match on overlap between (1) and (2) first; then filter/rank by (3).
- The response must include plain-language reasoning citing the actual matched interests (e.g. "Dr. Okoye lists NLP and computer vision; student's stated interest is NLP-based recommendation systems; Dr. Okoye currently supervises 2, capacity is 4").
- Admin still confirms in the existing assignment UI.

### Tasks

#### Backend

- [x] Add an admin-only recommendation endpoint accepting one unassigned student/project ID and a bounded result limit.
- [x] Scope candidates to approved supervisors in the same department/session and exclude supervisors at capacity.
- [x] Replace taxonomy/tag-based scoring with naive overlap between supervisor `areas_of_expertise` and student `project_interests` (free-text or comma-separated tags); same-department filter and capacity exclusion still apply.
- [x] Make ordering stable and make “no suitable supervisor” a valid result.
- [x] Keep the existing assignment endpoint as the only write path and revalidate availability/capacity there to prevent stale-recommendation races.
- [x] Add `User.areas_of_expertise` (supervisor) and `User.project_interests` (student) free-text fields with migration.
- [x] Add `GET /api/profile/` and `PUT /api/profile/` for self-service profile editing with bounded string validation.
- [x] Add `GET /api/admin/supervisor-workload/` returning each supervisor's expertise alongside load/capacity.
- [x] Add `GET /api/admin/student-interests/` returning each unassigned student's `project_interests`.

#### Frontend/WebMCP and confirmation UI

- [x] Register `suggest_supervisor_assignment` only in the admin layout with `readOnlyHint: true`.
- [x] The tool must never call `POST /api/assign-supervisor/` or return an auto-execution token.
- [x] Allow a recommendation to preselect/highlight a supervisor in the existing assignment page only after the admin opens the UI; preserve the existing modal and explicit Assign click.
- [x] Show score factors/reasoning in the confirmation UI and refresh/revalidate candidates before committing.
- [x] Add a supervisor profile editor (`areas_of_expertise`) on the supervisor dashboard.
- [x] Add a student profile editor (`project_interests`) on the student dashboard.

### Required tests

- [x] Expertise match, workload balance, capacity exclusion, unapproved/cross-department exclusion, tie ordering, no tags, and no candidates.
- [x] Non-admin and anonymous access denied; assigned or inaccessible student rejected.
- [x] Recommendation performs no writes (database state assertion and HTTP-method/tool-spy assertion).
- [x] Recommendation reasoning cites the actual matched interests from the new profile fields.
- [x] Profile endpoints validate string length and reject non-strings.
- [ ] Assignment endpoint detects a supervisor becoming full after recommendation.
- [ ] UI requires an explicit human click and displays a recoverable stale-result error.

### Manual acceptance

Invoke the tool for an NLP project after supervisors have declared expertise and the student has declared project_interests; inspect ranked workload/expertise facts, open the assignment UI, and confirm no assignment exists until the admin clicks Assign.

### Exit gate / rollback boundary

Recommendations and their optional UI display can be removed while the original manual assignment workflow remains functional.

---

## Milestone 8 — Viva/Defense Prep Quizzer

**Tool:** `generate_defense_questions`  
**Outcome:** A student's agent receives grounded, private evidence from that student's work and feedback from which to conduct a tailored defense quiz.

### Tasks

#### Backend

- [ ] Add a student-only defense-prep endpoint that derives the student from `request.user` and uses only their current-session project.
- [ ] Select approved/latest chapter text and the student's own review history; never accept another student ID.
- [ ] Deterministically extract bounded question seeds from section headings, key sentences/terms, project objectives/methods/results, unresolved feedback themes, and revision warnings.
- [ ] Return each seed with category, difficulty, source type/record/section, concise evidence, rationale, and optional expected talking points. Do not claim generated answers are authoritative.
- [ ] Accept bounded milestone/category/difficulty/count filters. Explicitly report insufficient/extraction-unavailable source material.

#### Frontend/WebMCP

- [ ] Register `generate_defense_questions` only in the student layout.
- [ ] Describe how the calling agent should turn seeds into one-at-a-time questions, wait for answers, and ground follow-ups in the supplied evidence.
- [ ] Do not expose supervisor-only notes or any other student's content.

### Required tests

- Seeds from content, feedback weak points, mixed sources, no feedback, no approved chapter, extraction failure, duplicate suppression, deterministic limits, and filter validation.
- Student A can never retrieve Student B's evidence; supervisor/admin/anonymous calls are denied unless a separate future policy is explicitly approved.
- Output provenance points only to the caller's permitted records.
- Tool role/schema/normalization tests and prompt-injection strings in document text remain inert data.

### Manual acceptance

Invoke for a student with methodology feedback and confirm the agent can ask a grounded methodology question, explain why it was selected, and continue as a quiz without exposing peer data.

### Exit gate / rollback boundary

The read-only preparation endpoint/tool can be removed without changing documents, reviews, or ordinary student workflows.

---

## Milestone 9 — Opt-in anonymized Cohort Benchmarking

**Tool:** `compare_my_progress`  
**Outcome:** An opted-in student can compare their progress with a privacy-protected current-session cohort without learning peer identities or records.

### Tasks

#### Privacy and backend

- [ ] Add an explicit student benchmarking opt-in preference, default `false`, with an ordinary authenticated settings UI/API to change it.
- [ ] Define the cohort as the caller's department and current academic session. Do not allow arbitrary cohort, student, supervisor, or department inputs.
- [ ] Establish a configurable minimum cohort threshold (recommended minimum: 5 eligible students excluding or consistently including the caller, documented in the contract). Suppress results below the threshold.
- [ ] Map progress to a documented ordered milestone/status scale and calculate aggregate counts/percentages, caller percentile/band, median stage, and percentage at-or-beyond each stage.
- [ ] Apply small-cell suppression and return rounded aggregates. Never return names, IDs, emails, matriculation numbers, titles, text, exact peer timestamps, or per-student rows.
- [ ] Return only the caller's exact stage; all peer information remains aggregate.

#### Frontend/WebMCP

- [ ] Register/enable `compare_my_progress` only for a student whose server-backed opt-in is active; unregister immediately after opt-out.
- [ ] Provide an opt-in explanation covering data used, aggregate output, minimum cohort behavior, and revocation.
- [ ] Keep the tool read-only; preference changes happen through the normal settings UI, not through WebMCP.

### Required tests

- Opted-out denial, opt-in/opt-out transition, minimum cohort suppression, small cells, rounding, milestone ordering, ended/current sessions, and no-project caller.
- Response-key allow-list and snapshot/schema tests prove forbidden peer identifiers/content cannot appear.
- Cross-department/session records do not affect aggregates.
- Tool registers only after confirmed opt-in and unregisters on opt-out/logout.

### Manual acceptance

With a cohort above the threshold, opt in and invoke the tool; inspect raw output to confirm it contains only aggregate peer values. Opt out and confirm the tool disappears.

### Exit gate / rollback boundary

Benchmarking can be disabled or removed without affecting project progress. Preference migration rollback behavior is documented.

---

## Milestone 10 — Cross-tool hardening, browser validation, deployment, and submission

**Outcome:** All six tools are secure, observable, deployable, and supported by reproducible hackathon evidence.

### Tasks

#### Automated integration and adversarial coverage

- [ ] Create a full role/tool matrix asserting exactly: supervisor gets feedback themes, chapter changes, and stalled students; admin gets stalled students and assignment suggestions; opted-in student gets defense questions and cohort comparison; no other registrations occur.
- [ ] Add contract tests for all input schemas, annotations, names, descriptions, result envelopes, output budgets, deterministic ordering, and empty/error states.
- [ ] Add adversarial fixtures containing prompt injection, HTML/script text, oversized values, Unicode, malformed IDs, unauthorized IDs, and stale/deleted records.
- [ ] Verify every tool is GET/read-only at the business level and makes no database writes during invocation.
- [ ] Add backend query-count/performance tests and indexes for representative cohort/review/submission volumes.
- [ ] Add end-to-end smoke coverage for login by role, tool-host mount, API invocation, token refresh, logout/unregistration, and the admin confirmation boundary. Use browser automation only after selecting and documenting a framework compatible with the project.

#### Deployment/security review

- [ ] Verify production CORS, allowed hosts, HTTPS cookies, CSRF assumptions, origin isolation, and `Permissions-Policy: tools=(self)` (plus only explicitly trusted origins if required).
- [ ] Remove hard-coded production secrets; load them from environment and run Django's deployment checks.
- [ ] Confirm logs contain request/tool names and safe status metadata but no document text, feedback, tokens, or personal output.
- [ ] Add rate limits/throttling and timeouts appropriate to expensive diff/analysis endpoints.
- [ ] Verify the frontend production build uses the deployed DRF URL and authenticated requests work across the actual origins.

#### Required real-browser validation

- [ ] In a supported Chrome/Chrome Canary configuration, use the Model Context Tool Inspector to verify tool discovery, JSON schemas, manual invocation, structured output, and errors for every permitted role.
- [ ] Verify tools are absent for wrong roles, after logout, after opt-out, and on public/auth pages.
- [ ] Test representative natural-language prompts in ChatGPT desktop's built-in browser for all six tools.
- [ ] Record browser/version/flag or origin-trial configuration and results in a repeatable test checklist. Note that WebMCP is experimental and may change.

#### Submission deliverables

- [ ] Add an OSI-approved `LICENSE` and ensure it is visible/configured in the public GitHub repository About section.
- [ ] Publish the live Vercel frontend and production backend; run post-deployment smoke tests.
- [ ] Write the submission description: why WebMCP fits, UX improvement, newly possible workflows, agent-native architecture, security/privacy boundaries, and testing.
- [ ] Produce a demo seed command/data set containing fictional users and deterministic examples for all six tools.
- [ ] Record a narrated demo under three minutes showing role-scoped discovery and at least the strongest tools end-to-end, including human confirmation for assignment.
- [ ] Publish a limitations section covering deterministic heuristics, scanned PDFs, minimum cohort suppression, browser availability, and the fact that agent narration must be verified by users.

### Required tests

- Entire backend and frontend suites pass from a clean checkout/database.
- Lint and production build pass with no ignored new errors.
- All schema, security, privacy, performance, and end-to-end checks above pass.
- Deployment smoke tests pass against production, not only localhost.

### Manual acceptance

Run the documented release checklist from a clean browser profile as admin, supervisor, student opted out, and student opted in. Capture evidence for every role/tool registration and representative invocation.

### Exit gate / rollback boundary

The release is tagged only after automated and real-browser gates pass. Each tool has a documented feature-disable/removal path; disabling one tool does not disable unrelated dashboards or tools.

---

## Requirement traceability

| Requirement                                                                     | Primary milestone(s) |
| ------------------------------------------------------------------------------- | -------------------: |
| Automated test foundation and authorization baseline                            |                    1 |
| Session, expertise/capacity, contact, review, revision, and extracted-text data |                    2 |
| WebMCP API/hook, lifecycle, schemas, role registration, security annotations    |                    3 |
| `get_recurring_feedback_themes`                                                 |                    4 |
| `explain_chapter_changes`                                                       |                    5 |
| `find_stalled_students`                                                         |                    6 |
| `suggest_supervisor_assignment` with human-confirmed write                      |                    7 |
| `generate_defense_questions`                                                    |                    8 |
| `compare_my_progress` opt-in/anonymized                                         |                    9 |
| Inspector and ChatGPT desktop validation                                        |                   10 |
| Vercel/live deployment, OSS license, demo video, written submission             |                   10 |

## Recommended delivery discipline

For each milestone:

1. Create a focused branch and convert its checkboxes into tracked issues/subtasks.
2. Write authorization/contract tests before the endpoint or tool implementation.
3. Keep migrations, backend service, endpoint, frontend adapter, and tests in reviewable commits.
4. Run the full definition-of-done suite, not only milestone-specific tests.
5. Demonstrate the manual acceptance scenario and save non-sensitive evidence.
6. Merge only when the milestone exit gate is met; do not start a second half-finished tool.
