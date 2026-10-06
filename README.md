# Local Research Assistant + Study Buddy Hybrid

A desktop AI application for interacting with personal study materials, research papers, notes, and PDFs using Retrieval Augmented Generation (RAG).

The project combines two major workflows:

* **Research Assistant** — ask questions about your documents and receive answers with citations.
* **Study Buddy** — generate summaries, flashcards, quizzes, and revision material from imported content.

---

# Project Status

🚧 Early Development

Current Phase:

* Project setup
* Architecture planning
* Environment preparation

---

# Project Vision

Students and researchers repeatedly upload the same documents to online AI tools.

This project aims to create a local knowledge workspace where users can:

* Import documents once.
* Search and chat with them anytime.
* Generate study material automatically.
* Build a searchable personal knowledge base.

The goal is to reduce friction while studying and researching.

---

# Learning Project Declaration

This project is intentionally designed as a learning project.

Development decisions prioritize:

1. Understanding over speed.
2. Simplicity over optimization.
3. Readability over cleverness.
4. Modular design over shortcuts.

Every subsystem should be understandable and explainable by the developer.

No component should be treated as a black box.

---

# Planned Features

## Research Mode

* Document import
* Question answering
* Source citations
* Cross-document comparison
* Topic summaries

## Study Mode

* Flashcard generation
* MCQ generation
* Revision summaries
* Key concept extraction
* Short answer questions

---

# MVP Scope

Included:

* PDF import
* DOCX import
* Semantic search
* RAG-based question answering
* Flashcard generation
* Summary generation

Excluded from MVP:

* Cloud synchronization
* User accounts
* Collaboration features
* Mobile applications
* Local LLM execution
* OCR for handwritten notes

---

# Architecture Overview

Documents
→ Document Processing
→ Chunking
→ Embeddings
→ Vector Database
→ Retrieval Engine
→ Prompt Construction
→ LLM Response
→ User Interface

---

# Planned Technology Stack

| Layer               | Technology             |
| ------------------- | ---------------------- |
| UI                  | PySide6                |
| Language            | Python 3.12            |
| Document Processing | PyMuPDF, python-docx   |
| Embeddings          | sentence-transformers  |
| Vector Database     | ChromaDB               |
| Database            | SQLite                 |
| LLM Provider        | OpenAI-compatible APIs |
| Testing             | pytest                 |
| Formatting          | black                  |
| Linting             | ruff                   |
| Type Checking       | mypy                   |

---

# Development Roadmap

## Phase 0

Research and architecture planning.

## Phase 1

Desktop application foundation.

## Phase 2

Document import and processing.

## Phase 3

Embeddings and semantic retrieval.

## Phase 4

Research assistant functionality.

## Phase 5

Study buddy functionality.

## Phase 6

Packaging and Microsoft Store release.

---

# Repository Structure

```text
app/
├── core/         # settings, paths, background task framework
├── database/     # engine, sessions, Alembic migrations
├── documents/    # document import and storage
├── workspace/    # workspace management
├── knowledge/    # (planned) knowledge base
├── study/        # (planned) study tools
└── ui/           # PySide6 windows, pages, widgets

tests/            # mirrors the app/ feature folders
data/             # local runtime data (database, documents, cache)
```

Each feature folder follows the same layers:

```text
domain/  dto/  mapper/  orm/  repository/  services/
```

---

# Success Criteria

The project succeeds if:

* The developer understands every subsystem.
* The architecture can be explained in interviews.
* The application solves a real problem.
* The application reaches production quality.
* The application is released publicly.

Revenue is desirable but not required for project success.

The primary product is not the software.

The primary product is the developer skill gained while building it.

---

# License

License selection pending.

---

# Author

Developed as a personal learning project focused on:

* Desktop application development
* Retrieval Augmented Generation (RAG)
* Vector databases
* AI application architecture
* Software engineering best practices