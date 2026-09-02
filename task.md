

Here is what we want to achieve:


**1. Supervisor Feedback Pattern Analyzer**
Tool: `get_recurring_feedback_themes` — a supervisor's agent scans everything they've written across *all* their students this session and surfaces "you've flagged citation formatting issues in 6 of 8 submissions" or "three students are struggling with the same methodology section." This turns a supervisor's own scattered comments into a teaching insight they'd never notice manually — genuinely impossible to see without an agent aggregating across submissions.

**2. Cross-Student Workload Balancer (Admin)**
Tool: `suggest_supervisor_assignment` — instead of admin manually matching, the agent looks at each supervisor's current student count, their research area/expertise tags, and the student's project topic, then proposes the best-fit pairing with reasoning ("Dr. Okoye already supervises 2 NLP projects and has capacity"). Admin still confirms, but the matching logic — which is currently just admin's memory/gut feel — becomes structured and explainable.

**3. Silent Student Flagging (Admin + Supervisor)**
Tool: `find_stalled_students` — cross-references submission timestamps across the whole department: "these 4 students haven't submitted anything in 3+ weeks, and their supervisors haven't logged any contact either." This is the kind of thing that falls through the cracks in a real department — nobody's job to check, but an agent can watch it continuously.

**4. Revision Diff Narrator**
Tool: `explain_chapter_changes` — instead of a supervisor re-reading a whole resubmitted chapter, the agent explains *in prose* what actually changed since the last version and whether previous feedback points were addressed ("addressed the methodology concern, citation issue from last review still present"). This turns a review that takes 20 minutes into a 2-minute confirmation.

**5. Viva/Defense Prep Quizzer (Student)**
Tool: `generate_defense_questions` — pulls a student's own chapter content plus their supervisor's actual feedback history, then quizzes them on likely defense questions targeted at *their specific weak points*, not generic questions. This is personal, uses data that only exists inside UniTrack, and genuinely couldn't happen without the tool having structured access to both the document and the feedback trail.

**6. Cohort Benchmarking (Student, opt-in/anonymized)**
Tool: `compare_my_progress` — a student's agent can check "am I behind where students usually are at this point in the session" using anonymized aggregate data (e.g., percentage of cohort that's submitted chapter 3 by this week). Currently a student has zero visibility into whether they're on pace — this gives them a signal without exposing anyone else's actual work.

My pick for "most creative but still shippable": **#1 (Feedback Pattern Analyzer)** or **#4 (Revision Diff Narrator)** — both use data UniTrack already has (submission history + feedback text), both produce something a human genuinely couldn't do by hand in reasonable time, and both fit the "meaningfully better together" framing cleanly since the agent isn't replacing the supervisor's judgment, just compressing the busywork around it.
