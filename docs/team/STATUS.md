# Project status

**Updated:** 2026-10-08 · **Stage:** 🚧 Demo Gate 1 (after v0.3) ·
**Latest release:** [v0.3.2](https://github.com/AzureSky0/Local-Research-Assistant-and-Study-Buddy-Hybrid/releases/tag/v0.3.2)

> Update this page at least weekly and after every release. Keep the
> history short: move old "Recently done" items into the changelog
> section at the bottom.

## Where we are

```text
v0.1 Foundation ─── v0.2 Workspaces & Documents ─── v0.3 Knowledge Engine ─── 🚧 Demo Gate 1 ─── v0.4 AI Assistant ─── v0.5 Prototype ─── 🚧 Demo Gate 2
      ✅                        ✅                           ✅                     ◀ we are here
```

The document workflow (import → read → search → open at page) is
complete and released to testers as a Windows app. **Feature work is
paused** while testers try it; only fixes from their feedback go in.

## Current focus

| Work | Owner | State |
|---|---|---|
| Recruit 3–5 testers and run Demo Gate 1 sessions | Akshat | 🟡 Starting |
| Record feedback in [FEEDBACK_LOG.md](FEEDBACK_LOG.md) | Whoever runs the session | 🟡 Starting |
| Fix "before v0.4" feedback items, publish 0.3.x | Team | ⏳ After sessions |
| Choose the final product name | Akshat | ⏳ Before public release |

## Next (v0.4 — AI Assistant), after Demo Gate 1

1. **Local model benchmark** — which runtime (Ollama or llama.cpp) and which
   model sizes give good cited answers fast enough on 8 GB and 16 GB laptops.
2. **Ask section** in each workspace, separate from the Library: retrieve
   passages → write an answer only from them → check each claim against
   its source → cite document and page (click opens the page).
3. Conversation history per workspace.

## Progress so far

| Version | Goal | Result |
|---|---|---|
| v0.1 Foundation | Architecture, database, tooling | ✅ Layered architecture, SQLite + SQLAlchemy + Alembic, ruff/mypy/pytest |
| v0.2 Workspaces & Documents | Organize documents | ✅ Workspaces, file/folder import, duplicate detection, progress and time left, UI redesign |
| v0.3 Knowledge Engine | Find anything, fast | ✅ Text extraction, keyword search, passages, search by meaning, hybrid ranking, open at page, background status, Windows package |

### Key numbers (benchmark: 358 arXiv papers, 9,972 pages, 45 questions)

| Measure | Result | Target |
|---|---|---|
| Correct paper in top 5 — hybrid search | **87%** (standard 100%, hard 67%) | — |
| Correct paper in top 5 — words only / meaning only | 78% / 84% | — |
| Reading a typical PDF (median) | 0.14 s | < 5 s ✅ |
| All 358 papers keyword-searchable | ~3 min | — |
| All 358 papers ready for search by meaning | ~32 min on a 16 GB laptop | < 30 min ⚠️ close |
| Keyword search | < 100 ms | < 100 ms ✅ |
| Search by meaning (vector lookup) | ~33 ms median | < 300 ms ✅ |
| Random text finds nothing | ✅ (evidence check) | — |
| Automated tests | 270 passing | all passing ✅ |

## Known issues and technical debt

Good first tasks are marked ⭐.

| Item | Impact | Notes |
|---|---|---|
| Windows shows "unknown publisher" warning | Testers must click "More info → Run anyway" | Code signing before public release |
| No app icon ⭐ | Generic icon in taskbar | Add icon to window and `packaging/loci.spec` |
| A search sharing **no** words with any document finds nothing, even by meaning | Rare for real questions | Deliberate trade-off against false matches (see DECISIONS.md, search evidence) |
| Embedding runs in a thread, not a separate process | UI can feel slower on 4-core laptops during first indexing | Decision 033 plans a worker process |
| Processing commits per stage | Slower bulk import | Batch commits |
| Search runs on the UI thread | A rare slow search (~0.4 s) briefly freezes the window | Move to a background worker |
| Unused `chroma/` folder created in the data folder ⭐ | Clutter | Remove from `REQUIRED_DIRECTORIES` |
| Fonts not bundled (IBM Plex) ⭐ | UI falls back to system fonts | Bundle with the app |
| UI polish | Spacing and wording | Waiting for tester feedback |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Local AI models too slow or inaccurate on 8 GB laptops | Medium | Benchmark before building v0.4; smaller models on Light profile; answers labelled when uncertain |
| Name conflict with existing apps | High (many names taken) | Working name only; check stores and trademarks before release |
| Testers not representative (only developers) | Medium | Recruit students and researchers outside the team |
| Scanned PDFs are common for some users | Medium | Detect "no text" and explain; OCR extension later |

## Changelog

- **2026-10-23** — v0.3.3 in testing (branch `feature/windows-installer`):
  a Windows installer that updates an installed older version in place
  (no admin rights, Start-menu entry, uninstaller, library kept), asks to
  close Loci first, warns before a downgrade, and a database backup before
  a new version changes the library's format.
- **2026-10-23** — v0.3.2 released after the first tester session: only one
  copy runs at a time (fixes "database is locked" on first start), a
  "Starting…" window, plain start-up error messages, no red low-memory alarm
  when idle, fewer irrelevant "by meaning" results, contents pages ranked
  last. The zip now includes a licenses folder (AGPL-3.0). Repository public
  since 2026-10-21.
- **2026-10-08** — v0.3.1 released: home page document counts update after
  imports; status panel and Settings no longer cut off text at high display
  scaling. Team handbook and public project overview (PDF) added.
- **2026-10-07** — v0.3.0 released as a Windows zip; working name Loci;
  branches merged into `main`. Benchmark, search by meaning with hybrid
  ranking, computer profile, status indicator with time left; random
  text no longer matches documents.
- **2026-10-06** — UI redesign; staged background reading; keyword
  search; open at page; passages (chunks).
