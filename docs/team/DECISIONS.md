# Decisions

Why things are the way they are. Each decision has a number that never
changes; when a decision is replaced, the old one stays and points to the
new one. The full log (context, alternatives, consequences) is kept by
the project lead; this page summarizes what the team needs.

## How to propose a decision

Add an entry at the end of this file in the pull request that makes the
change, using this shape, and mention it in the pull request description:

```markdown
### 042 — <Title>
**Status:** Proposed / Accepted (YYYY-MM-DD) · **Replaces:** —
**Context:** what problem forced a choice.
**Decision:** what we chose, in a few bullet points.
**Why:** the main reason, and the strongest alternative we rejected.
**Consequences:** what gets easier, what gets harder.
```

Choices about models, storage or performance need **measurements**
(benchmark or a reproducible test), not opinions.

---

## Product

| # | Decision | In short |
|---|---|---|
| 001 | Knowledge-first application | The core is understanding documents; AI is a layer on top. |
| 002 | Desktop-first | A desktop app, not a website: local files, offline, private. |
| 003 | Workspace-first workflow | Everything lives in workspaces (one per subject or project). |
| 004 | Local-first | Data stays on the user's computer; no accounts. |
| 005 | The app does the thinking | Users never need to know about chunks, models or indexes. |
| 011 | Knowledge packs are app-wide | Installed packs serve every workspace. |
| 012 | Version-based development | Versions with one goal each; Demo Gates for user feedback. |
| 021 | Duplicates per workspace | The same file may be in several workspaces; duplicates detected within one (by checksum). |
| 022 | Core formats | PDF, plain text, Markdown in the core; others as extensions. |
| 023 | One shared core | No student or researcher editions; audience-neutral wording. |
| 036 | Local-only AI for now | No document content sent to cloud AI. Runtime and models chosen by benchmark before v0.4. |
| 037 | Computer profile + workspace focus | Profile (Light/Standard, detected from RAM) sets the ceiling; workspace focus (look up & explain / study & analyze) chosen per workspace. The lower of the two applies. |
| 038 | Accuracy and source rules | Answers only from retrieved passages; every claim cited (document, page) and checked; "not in your documents" instead of guessing; code computes numbers, the AI describes. |
| 039 | Structured extraction; exam workflow in v0.6 | Collection-wide analysis turns documents into tables first (e.g. one row per exam question), then analyzes in code. |
| 041 | Working name "Loci"; Demo Gates as planned | Final name later. Demo Gate 1 after v0.3, Demo Gate 2 after v0.5. |
| 042 | Licence: AGPL-3.0 with an extension exception | Loci is AGPL-3.0 (compatible with PyMuPDF, keeps the project open). Extensions that use only the public extension interface may use any licence. The copyright holder keeps the option of commercial licences; core contributions will need a contributor licence agreement. Community extensions arrive in phases: data packs first, code extensions only after permissions, isolation and review exist. |

## Architecture

| # | Decision | In short |
|---|---|---|
| 006 | Layered modular architecture | UI → Managers → Services → Repositories. |
| 007 | Responsibility-based modules | Folders by feature (`documents`, `knowledge`, …), same layers inside each. |
| 008 | Knowledge engine separate from AI | Search and indexing work without any AI model. |
| 009 | Repository pattern | Only repositories touch the database; services own transactions. |
| 010 | Background-first processing | Slow work never blocks the UI; it is cancellable and resumable. |
| 024 | Structured content, template rendering | Generated content is data rendered by templates (styling as extensions). |
| 025 | Extension tiers | VS Code-style extensions: formats, subjects, outputs; heavy ones out-of-process. |
| 026 | Plugin API boundary | Extensions use a stable, versioned API, never internal code. |
| 027 | Knowledge pack kinds | Dictionaries, reference data, formula sheets, … |
| 028 | Capability registry | Features are found by capability (`document.pdf.read`), so extensions can add them. |
| 029 | Per-user data folder | `%LOCALAPPDATA%\Loci`, override `LOCI_DATA_DIR`. |
| 031 | Staged, resumable processing | Register → extract → keyword index → chunk → embed; each stage stored; searchable by words first. |
| 032 | Layered workspace memory | Source knowledge, document cards, workspace overview, conversation memory, saved knowledge — visible and editable. |
| 033 | Storage and concurrency for scale | SQLite WAL; sqlite-vec preferred; CPU-heavy work in a worker process *(not yet built)*. |

## Technology

| # | Decision | In short |
|---|---|---|
| 013 | SQLite | One local file, transactional, no server. |
| 014 | UUID primary keys | Safe for future export, sync and merging. |
| 015 | SQLAlchemy ORM | Typed models, clear queries. |
| 016 | Alembic migrations | Every schema change is a migration; run automatically at start-up. |
| 017 | PySide6 (Qt) | Native desktop UI in Python. |
| 018 | Python | One language for UI, data and AI. |
| 019 / 020 | Markdown, living documentation | Docs in Markdown, kept current with the code. |
| 030 | AI provider interface | Kept so an opt-in cloud provider can be added later *(provider choice replaced by 036)*. |
| 034 | Performance targets and benchmark | Keyword < 100 ms, meaning < 300 ms, PDF searchable < 5 s, 300 PDFs embedded < 30 min, UI never freezes, idle < 500 MB. 358 arXiv papers as the benchmark. |
| 035 | Embeddings, vectors, hybrid search | fastembed (ONNX, no PyTorch); arctic-embed-xs (Standard) / potion-retrieval-32M (Light); sqlite-vec; hybrid with reciprocal rank fusion. Chosen by benchmark. |
| 040 | Subject and format plugins | OCR, more formats, maths/chemistry/engineering support as plugins after v0.6. |

## Smaller decisions recorded in code history

| When | Decision | Why |
|---|---|---|
| 2026-10-07 | **Search evidence check:** a page must contain ≥30% of a search's meaningful words; meaning-only results only from supported documents. | Random text matched every document. Measured: all hard benchmark questions still found; unrelated searches return nothing. Rerankers were tried and rejected (≈2 s per search, unreliable). |
| 2026-10-07 | **Windows package with PyInstaller**, distributed as a zip on GitHub Releases. | Testers should not need Python or a terminal. |
| 2026-10-06 | **Short searches need all words; longer ones match pages with some of the words, best first.** | Questions rarely have every word on one page. |
