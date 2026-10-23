# Feedback log — Demo Gate 1

One row per tester session, then one row per finding. Keep the testers'
own words where possible. Do not record personal data beyond a first
name or initials.

Guide used: [../demo/DEMO_GATE_1.md](../demo/DEMO_GATE_1.md) · Version:
v0.3.x (note the exact version per session) · Goal: 3–5 testers who are not on the team.

## Sessions

| # | Date | Tester (initials) | Role (student, researcher, …) | Documents (number, type) | RAM | Version | Run by |
|---|---|---|---|---|---|---|---|
| 1 | 2026-10-22 | Y. | Master's student (Discrete Optimization) | 6 PDFs, lecture notes | 11 GB | 0.3.1 | Self-run at home; feedback by screenshots |
| 2 | | | | | | | |
| 3 | | | | | | | |

## Ratings (1 hard – 5 easy)

| Statement | #1 | #2 | #3 | #4 | #5 | Average |
|---|---|---|---|---|---|---|
| Adding documents was easy | | | | | | |
| Organizing into workspaces made sense | | | | | | |
| Search found what I was looking for | | | | | | |
| Search felt fast | | | | | | |
| I understood what the app was doing in the background | | | | | | |
| I could use the app without explanation | | | | | | |

## Task results

✅ done alone · 🟡 done with hesitation (> 10 s) · ❌ needed help

| Task | #1 | #2 | #3 | #4 | #5 |
|---|---|---|---|---|---|
| 1. Create a workspace | ✅ | | | | |
| 2. Add files, then a folder | ✅ | | | | |
| 3. Add a file twice | | | | | |
| 4. Understand background progress | | | | | |
| 5. Find a known word | ✅ ("edmond karp") | | | | |
| 6. Find an idea in own words | | | | | |
| 7. Search nonsense | | | | | |
| 8. Open a result at its page | ✅ (opened in Edge at the page) | | | | |
| 9. Second workspace, switch | | | | | |
| 10. Pause and resume | | | | | |

## Findings

**Severity:** 🔴 blocks the task · 🟠 confusing or slow · 🟢 nice to have.
**When:** *before v0.4* (fix in 0.3.x) or *later*.

| # | Finding (tester's words where possible) | Session(s) | Severity | When | Issue / PR | Status |
|---|---|---|---|---|---|---|
| F1 | First start: three "Unhandled exception … database is locked" error windows before the app opened | 1 | 🔴 | before v0.4 | fix/tester-feedback-1 | Fixed: one copy per data folder (second start brings the window forward), "Starting…" splash, plain error message instead of a traceback. Reproduced by starting 3 copies at once. |
| F2 | Status pill showed a red "Paused — low memory" while the panel said "All caught up — nothing running" (10.0 of 11.2 GB in use by other apps) | 1 | 🟠 | before v0.4 | fix/tester-feedback-1 | Fixed: when nothing is waiting it says "All caught up" with an amber dot and a calm note |
| F3 | Search "edmond karp": two irrelevant "by meaning" passages (rounding weights, k-cliques) ranked above the real match | 1 | 🟠 | before v0.4 | fix/tester-feedback-1 | Fixed: meaning-only passages must share at least one search word. Benchmark unchanged (25/25, 19/20, 35/45 first); irrelevant meaning results for name searches 22 → 6 |
| F4 | The only word match shown was the table-of-contents line; the real pages were under "3 more matching pages" | 1 | 🟠 | before v0.4 | fix/tester-feedback-1 | Fixed: contents pages (dot leaders) rank after the document's other matching pages |
| F5 | "She thinks it is useful to her and a good product" | 1 | 🟢 | — | — | Positive |

## Searches that went wrong

Exact text matters — these become benchmark or test cases.

| Search text | Expected | Got | Session |
|---|---|---|---|
| edmond karp | Section pages about the Edmonds-Karp algorithm | Two unrelated passages by meaning, then the contents page | 1 |

## Summary (fill in at the end of the gate)

- **Is document import intuitive?**
- **Is workspace organization clear?**
- **Is searching fast enough?**
- **Can new users understand the workflow?**
- **Top 3 fixes before v0.4:**
- **Decision:** proceed to v0.4 / fix first.
