# Loci

**Your local knowledge bank.** A desktop app for working with a large
collection of your own documents (papers, books, notes) — entirely on your
computer. Import documents into workspaces, then find anything in them by
words or by meaning, and jump straight to the right page.

Everything runs locally: your documents never leave your computer, and
after a one-time model download the app works offline.

---

# Status

**v0.3 — Knowledge Engine (complete). Now at Demo Gate 1:** feature work is
paused while testers try the document workflow (importing, organizing,
searching). See [docs/demo/DEMO_GATE_1.md](docs/demo/DEMO_GATE_1.md).

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
cites the pages.

Not yet supported: scanned PDFs (no OCR), Word files, cloud sync.

---

# Running the app

**Easiest (Windows, no Python needed):** download `Loci-<version>-windows.zip`
from the [Releases page](https://github.com/AzureSky0/Local-Research-Assistant-and-Study-Buddy-Hybrid/releases), extract it, and double-click
`Loci.exe`. Windows may warn that the app is unsigned: **More info → Run
anyway**.

**From source:** Windows 10/11 (macOS and Linux should work but are
untested), Python **3.12**, about 1 GB of free disk space, 8 GB RAM
recommended.

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

Your data (the database with the text of your documents, logs, models) is kept in
the per-user app data folder — `%LOCALAPPDATA%\Loci` on
Windows (an earlier `LocalResearchAssistant` folder is moved there
automatically). To use a different folder (for example to try the app without
touching your real data), set `LOCI_DATA_DIR` before starting:

```powershell
$env:LOCI_DATA_DIR = "D:\loci-test-data"
python -m main
```

---

# Development

**Team handbook:** [docs/team/](docs/team/README.md) — project overview,
current status, roadmap, architecture, development guide, decisions,
testing, releases and meeting notes.

```powershell
pytest            # all tests (UI tests run headless)
ruff check app tests
mypy app
```

For detailed logs while developing, put `DEBUG=true` in a `.env` file in
the project folder.

To build the Windows app (`dist/Loci/Loci.exe` and a zip to share):

```powershell
pip install pyinstaller
python scripts/build_windows.py
```

The build is defined in `packaging/loci.spec`. Test the result on a
computer (or in a folder) without Python before sharing it.

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
Import → checksum (files stay where they are) → extract text per page → keyword index (SQLite FTS5)
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

# Name

*Loci* is a working name. It comes from the method of loci — the memory
palace, where knowledge is remembered by the place it is kept: workspaces
are the rooms, and every answer points back to its place, the page. A
final product name will follow.

The repository keeps its original name, Local Research Assistant + Study
Buddy Hybrid.

---

# Licence

Loci is free software, licensed under the **GNU Affero General Public
License v3.0** ([LICENSE](LICENSE)). You may use, study, share and change
it; if you share a modified version (including running it for others over
a network), you must make its source code available under the same
licence.

- **Extensions** that use only Loci's public extension interface may use
  any licence: see [LICENSE-EXTENSION-EXCEPTION.md](LICENSE-EXTENSION-EXCEPTION.md).
- **Third-party components** keep their own licences:
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Every Windows package
  includes their full licence texts in its `licenses` folder.
- **Commercial licensing:** if the AGPL does not fit your use, other
  licensing terms may be available from the copyright holder; please open
  an issue to ask.

Copyright © 2026 Akshat Manojkumar Sahu.

---

# Learning project

This is intentionally a learning project: understanding over speed,
simplicity over optimization, readability over cleverness. Every subsystem
should be explainable by its developer — no black boxes.
