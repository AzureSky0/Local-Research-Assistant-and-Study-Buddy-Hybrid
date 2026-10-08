# Architecture

How Loci is built, as of v0.3. For the reasons behind each choice see
[DECISIONS.md](DECISIONS.md).

## Big picture

```text
┌──────────────────────────────── Desktop app (PySide6 / Qt) ────────────────────────────────┐
│  UI: windows, pages (Home, Library, Activity, Settings), widgets, status indicator          │
│        │ calls                        ▲ Qt signals (always delivered on the UI thread)       │
│  Managers: workspaces, library/search, imports, processing, embedding, background status   │
│        │ run work on background threads (AsyncTaskExecutor), report progress              │
│  Services: application logic, own the database transactions                                │
│        │                                                                                   │
│  Repositories: database access only (never commit)                                        │
└────────┼───────────────────────────────────────────────────────────────────────────────────┘
         ▼
  SQLite database (WAL)  ── tables, FTS5 keyword index, sqlite-vec vector index
  Data folder            ── copies of imported documents, models, logs
```

Everything runs on the user's computer. The only network access is the
one-time download of the search model.

## Code layout

```text
main.py                 # start-up: data folder, logging, database, managers, main window
app/
├── core/               # paths, settings, background tasks, computer profile, system monitor, time estimates
├── database/           # engine (SQLite settings, sqlite-vec), sessions, Alembic migrations
├── workspace/          # workspaces
├── documents/          # import, validation, storage, text extraction, processing pipeline
│   ├── extraction/     #   PDF (PyMuPDF) and text readers, registered by capability
│   └── processing/     #   staged pipeline: extract → keyword index → chunk
├── knowledge/          # keyword index, passages (chunks), embeddings, search
│   ├── embeddings/     #   model choice per computer profile, fastembed embedder
│   └── services/       #   keyword, hybrid (words + meaning), evidence check
├── study/              # placeholder for v0.6 study tools
└── ui/                 # windows, pages, dialogs, widgets, managers, theme
packaging/loci.spec     # Windows build (PyInstaller)
scripts/                # build script, search benchmark
tests/                  # mirrors app/; UI tests run headless
```

Each feature folder uses the same layers: `domain/` (plain objects),
`dto/` (data passed between layers), `mapper/`, `orm/` (SQLAlchemy
models), `repository/`, `services/`.

## Life of a document

```text
Import (background thread)
  validate type → copy into the data folder → checksum
  → duplicate in this workspace? skip : record as REGISTERED

Processing pipeline (one background worker, small files first, resumable)
  REGISTERED ──extract text per page──▶ EXTRACTED
             ──add pages to FTS5────▶ KEYWORD_INDEXED   ← searchable by words now
             ──split into passages──▶ CHUNKED            (≈220 words, 40-word overlap,
                                                           page range kept)

Embedding (separate background worker, batches of passages)
  passage text ──fastembed model──▶ vector ──▶ sqlite-vec table   ← searchable by meaning
```

- Each stage is stored per document, so after a crash or restart work
  continues where it stopped.
- The same file may be in several workspaces; duplicates are only
  detected within one workspace.
- Each passage records which model embedded it; switching the model
  (computer profile) re-embeds in the background.

## Life of a search

```text
search box (debounced) → LibraryManager → HybridSearchService   (runs on the UI thread; ~0.1 s)
  1. Keyword search (FTS5, bm25 ranking, snippets)
       short searches: all words must match; widened to any word if nothing does
       longer searches: pages with any of the words, best first
  2. Evidence check: a page must contain ≥30% of the meaningful words
  3. Search by meaning: embed the query → nearest passages (sqlite-vec, cosine)
       only from documents the words support, or passages that contain
       enough of the words themselves
  4. Reciprocal rank fusion of both lists, grouped by document (≤3 passages each)
  → results with page, highlighted excerpt, "by words" / "by meaning" / both
```

Why the evidence check: nearest-neighbour search always returns
*something*, and small models score unrelated text almost like related
text. Without the check, random text listed every document.

## Data storage

| What | Where |
|---|---|
| Workspaces, documents, pages, passages | SQLite tables |
| Keyword index | FTS5 virtual table `page_search` (porter stemming, accents ignored) |
| Vectors | sqlite-vec table per model, `chunk_vectors_<model>`, partitioned by workspace |
| Imported files | `<data folder>/documents/` |
| Search models | `<data folder>/models/` |
| Logs | `<data folder>/logs/app.log` |
| Preferences | `<data folder>/preferences.json` |

Data folder: `%LOCALAPPDATA%\Loci` (override with `LOCI_DATA_DIR`).
SQLite runs in WAL mode so searches are not blocked by background
writers. Deleting a document or workspace removes its index entries and
vectors through triggers and cascades.

## Background work and the computer

- Imports, reading and embedding run on separate background workers; the
  UI thread only receives signals.
- `BackgroundManager` checks the computer every 2 seconds (`psutil`):
  it shows health, estimates time left from recent pace, lets the user
  pause, and **pauses automatically below 1 GB of free memory** (resumes
  above 1.5 GB).
- **Computer profile:** Standard (≥ 12 GB RAM) uses
  `snowflake-arctic-embed-xs` (384 dimensions); Light uses
  `potion-retrieval-32M` (faster, lighter). Changeable in Settings.

## Extension points (for later)

- **Capability registry:** readers register as `document.<type>.read`;
  OCR and new formats will plug in the same way.
- Planned: pipeline stages from plugins, structured content with
  renderers, tools the AI can call, knowledge packs.

## Planned for v0.4 (not built yet)

```text
question → hybrid search → best passages → local LLM writes an answer
         → evidence check per claim → citations (document, page) → Ask page
```

Runtime and model chosen by benchmark (Ollama vs llama.cpp; sizes per
computer profile). Local only.

## Known gaps versus the design

- Embedding runs in a thread, not a separate worker process (planned).
- Search runs on the UI thread; slow searches (rare, up to ~0.4 s) briefly
  block the window. Move it to a background worker if it becomes noticeable.
- Knowledge is not yet stored in per-workspace folders (planned for
  export and backup).
- See [STATUS.md](STATUS.md) for the full list.
