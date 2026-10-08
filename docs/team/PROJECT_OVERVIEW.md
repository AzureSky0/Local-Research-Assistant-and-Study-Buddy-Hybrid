# Project overview

## In one sentence

**Loci** (working name) is a desktop app that turns a large collection of
your own documents into a private, searchable knowledge bank — and, from
v0.4, answers questions about them with page-level sources — entirely on
your own computer.

## The problem

Students and researchers work through a lot of documents: papers, books,
lecture notes, past exam papers. Today they:

- search file by file, or re-read to find "that passage I saw last week";
- upload the same documents to online AI tools again and again, with no
  memory between sessions and privacy concerns about what they upload;
- get AI answers they cannot easily check against the source.

## What we are building

A **local knowledge workspace**:

1. **Import once.** Add files or whole folders into workspaces (one per
   subject, project or book).
2. **Find anything.** Search by words and by meaning; every result points
   to the page it came from, and opens the document at that page.
3. **Ask** *(v0.4)*. Questions answered only from your documents, each
   claim checked against its source and cited with document and page.
4. **Study and analyze** *(v0.6 and later)*. Summaries, flashcards, quizzes,
   exam-paper analysis — added as needed, not forced on everyone.

## Who it is for

One shared core for everyone who reads a lot: students, researchers,
writers, professionals. We do **not** build separate "student" and
"researcher" editions; specialized needs (maths formulas, chemistry,
OCR for scanned pages, more file types) come later as installable
**extensions**, in the style of VS Code.

## Principles

| Principle | What it means in practice |
|---|---|
| **Local-first and private** | Documents and AI stay on the user's computer. After a one-time model download the app works offline. No accounts. |
| **Answers you can check** | Every result and answer shows its source page. If the documents do not contain the answer, the app says so instead of guessing. |
| **Works on ordinary laptops** | Designed for 8–16 GB RAM, no graphics card. The app detects the computer and picks lighter or stronger models. |
| **Searchable first, smarter later** | Documents become word-searchable within seconds; slower work (search by meaning, AI) finishes in the background without blocking the user. |
| **The app does the thinking** | Users should not need to understand chunks, embeddings or models. |
| **Learning project** | Understanding over speed, simplicity over cleverness. Every part should be explainable by the people who build it — no black boxes. |

## Scope today (v0.3.0)

**In:** workspaces; import of PDF, `.txt`, `.md` files and folders;
duplicate detection; background reading with progress and time left;
search by words and by meaning; open at page; computer profile; status
and pause controls; a packaged Windows app for testers.

**Not yet:** AI answers (v0.4), summaries, study tools, scanned PDFs
(OCR), Word/PowerPoint files, macOS/Linux packages, cloud sync,
collaboration, mobile.

**Never planned for 1.0:** user accounts, sending documents to a server
by default.

## How we work

- Development happens in **versions** (v0.1 … v1.0), each with a clear goal.
- At three **Demo Gates** we stop adding features and test with real
  users before continuing. We are at **Demo Gate 1** now.
- Every significant choice is recorded as a **decision** with its
  reasoning ([DECISIONS.md](DECISIONS.md)).
- Choices about models and storage are made by **benchmark**, not opinion
  (358 arXiv papers, 45 test questions).

## Name

"Loci" is a working name, from the *method of loci* (the memory palace:
knowledge remembered by the place it is kept). Many short names are
already taken by similar apps, so the final name will be chosen before
the public release. The repository keeps its original name, *Local
Research Assistant + Study Buddy Hybrid*.
