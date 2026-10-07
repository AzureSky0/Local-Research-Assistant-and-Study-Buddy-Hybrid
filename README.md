# Local Research Assistant + Study Buddy Hybrid

A desktop app for working with a large collection of your own documents
(papers, books, notes) — entirely on your computer. Import documents into
workspaces, then find anything in them by words or by meaning, and jump
straight to the right page.

Everything runs locally: your documents never leave your computer, and
after a one-time model download the app works offline.

---

# Status

**v0.3 — Knowledge Engine (complete). Now building v0.4 — AI Assistant.**
The first tester demo follows v0.4, so testers can try asking questions
and getting summaries as well as the document workflow. A draft tester
guide is in [docs/demo/DEMO_GATE_1.md](docs/demo/DEMO_GATE_1.md).

What works today:

* **Workspaces** — keep separate collections (one per course, project or
  book). The same file can be added to more than one workspace.
* **Import** — add files or whole folders (PDF, `.txt`, `.md`); duplicates
  within a workspace are detected; progress and time left are shown.
* **Reading in the background** — text is extracted page by page and
  indexed; you can keep working while it runs, and it resumes after a
  restart.
* **Search** — by words (fast, even with hundreds of documents) and by
  meaning (finds passages that say the same thing in other words). Results
  show the page and a highlighted excerpt; open a document at that page.
* **Status** — the bottom-right indicator shows background work, time
  left, and how busy the computer is; pause and resume at any time. Work
  pauses on its own when memory runs low.
* **Computer profile** — the app picks lighter or stronger local models
  for your computer automatically (Settings → This computer).

Coming next (v0.4): an **Ask** section where a local AI model answers
questions from your documents, checks each claim against its source, and
cites the pages; plus a short overview and summary of each document.

Not yet supported: scanned PDFs (no OCR), Word files, cloud sync.

---

# Running the app

Requirements: Windows 10/11 (macOS and Linux should work but are untested),
Python **3.12**, about 1 GB of free disk space, 8 GB RAM recommended.

```powershell
git clone https://github.com/AzureSky0/Local-Research-Assistant-and-Study-Buddy-Hybrid.git
cd Local-Research-Assistant-and-Study-Buddy-Hybrid

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python -m main
```

On first use the app downloads its search-by-meaning model (about 90 MB)
in the background. Search by words works immediately; search by meaning
starts once the model is ready. After that, no internet is needed.

Your data (database, copies of imported documents, logs, models) is kept in
the per-user app data folder — `%LOCALAPPDATA%\LocalResearchAssistant` on
Windows. To use a different folder (for example to try the app without
touching your real data), set `LRA_DATA_DIR` before starting:

```powershell
$env:LRA_DATA_DIR = "D:\lra-test-data"
python -m main
```

---

# Development

```powershell
pytest            # all tests (UI tests run headless)
ruff check app tests
mypy app
```

Database changes go through Alembic migrations (`app/database/migrations`);
the app upgrades the database automatically on start.

The search benchmark (358 arXiv papers, 45 questions) lives in
`scripts/benchmark/` and is how model and search choices were made.

## How it is built

```text
UI (PySide6 pages and widgets)
  → Managers (Qt objects; run work in the background, report progress)
    → Services (application logic; own the transactions)
      → Repositories (database access)
```

```text
Import → copy + checksum → extract text per page → keyword index (SQLite FTS5)
       → split into passages → embed (fastembed / ONNX) → vector index (sqlite-vec)
Search → words (FTS5, bm25) + meaning (nearest passages) → combined ranking
       → only pages that actually support the search are shown
```

| Layer             | Technology                                   |
| ----------------- | -------------------------------------------- |
| UI                | PySide6 (Qt 6)                               |
| Language          | Python 3.12                                  |
| Database          | SQLite (WAL) + SQLAlchemy 2 + Alembic        |
| Text extraction   | PyMuPDF                                      |
| Search by words   | SQLite FTS5                                  |
| Search by meaning | fastembed (arctic-embed-xs) + sqlite-vec     |
| Quality           | pytest, ruff, mypy                           |

```text
app/
├── core/         # settings, paths, background tasks, computer profile, system monitor
├── database/     # engine, sessions, Alembic migrations
├── documents/    # import, storage, text extraction, processing pipeline
├── workspace/    # workspaces
├── knowledge/    # keyword index, passages, embeddings, search
└── ui/           # windows, pages, widgets, managers

tests/            # mirrors the app/ folders
scripts/benchmark # search benchmark
```

Each feature folder uses the same layers:
`domain/  dto/  mapper/  orm/  repository/  services/`.

---

# Learning project

This is intentionally a learning project: understanding over speed,
simplicity over optimization, readability over cleverness. Every subsystem
should be explainable by its developer — no black boxes.
