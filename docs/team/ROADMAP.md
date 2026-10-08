# Roadmap

Development moves in versions, each with one clear goal and a success
test. At three **Demo Gates** feature work stops and real users try the
app before we continue. Dates are not fixed; a version is done when its
success test passes.

| | Version | Goal | Status |
|---|---|---|---|
| | **v0.1 Foundation** | A stable architecture to build on | ✅ Done |
| | **v0.2 Workspaces & Documents** | Organize documents | ✅ Done |
| | **v0.3 Knowledge Engine** | Find anything in your documents, fast | ✅ Done (v0.3.1 released) |
| 🚧 | **Demo Gate 1** | Validate the document workflow | ◀ **Now** |
| | **v0.4 AI Assistant** | Ask questions, get cited answers | Next |
| | **v0.5 First Public Prototype** | A complete, polished first experience | |
| 🚧 | **Demo Gate 2** | Validate the AI workflow | |
| | **v0.6 Study Tools** | Learn from your documents | |
| | **v0.7 Knowledge Packs** | Useful offline knowledge beyond your documents | |
| | **v0.8 Intelligence** | Proactive help | |
| 🚧 | **Demo Gate 3** | Validate the whole workspace | |
| | **v0.9 Polish** | Professional and reliable | |
| | **v1.0 Public Release** | Released to everyone | |

---

## ✅ v0.1–v0.3 (done)

Workspaces; import of files and folders with duplicate detection;
staged background reading (resumes after a restart); keyword search;
passages; search by meaning with hybrid ranking; open at page; computer
profile; background status with pause and time left; Windows package.

**Success test (v0.3):** questions retrieve the correct document context
quickly and accurately — met on the benchmark (87% correct paper in top
5, searches well under the time targets).

## 🚧 Demo Gate 1 — now

Questions we need answered by 3–5 testers who are not on the team:

- Is importing documents intuitive?
- Is organizing work into workspaces clear?
- Is searching fast enough, and does it find the right things?
- Can new users understand the app without help?

Tester guide: [../demo/DEMO_GATE_1.md](../demo/DEMO_GATE_1.md) ·
Feedback: [FEEDBACK_LOG.md](FEEDBACK_LOG.md).
**Exit:** feedback grouped; "before v0.4" items fixed and released.

## v0.4 — AI Assistant (next)

- **Local model benchmark first:** runtime (Ollama or llama.cpp) and model
  size per computer profile, measured on cited answers and explanations.
- **Ask section** per workspace, separate from the Library.
- Answers only from retrieved passages; **each claim checked** against its
  passage; **citations** with document and page; "not in your documents"
  when the answer is not there.
- Conversation history per workspace.
- Local only: no document content leaves the computer.

**Success test:** users can understand their documents without searching
manually.

## v0.5 — First Public Prototype

Stable document workflow, AI assistant, summaries, background processing,
UI polish. **Success test:** someone new can import documents, ask
questions, get useful answers and organize workspaces without help.

## 🚧 Demo Gate 2

Would users choose this over reading PDFs manually? Does it save time?
Is it easier than a web AI assistant?

## v0.6 — Study Tools

Flashcards, quizzes, summaries, study notes, revision mode, progress.
**Exam-paper workflow:** extract questions from past papers into a table
(marks, topic, difficulty with reasons), analyze patterns in code, and
generate practice papers that follow the same pattern.

## v0.7 — Knowledge Packs

Installable offline packs (language, science, developer) for answers
beyond the user's documents.

## v0.8 — Intelligence

Proactive suggestions: related documents, "compare these papers?",
recurring topics, reminders.

## 🚧 Demo Gate 3

Does the app feel genuinely helpful? Do suggestions help or distract?

## v0.9 Polish → v1.0 Public Release

Performance, accessibility, error handling, documentation; final name,
code signing, installer.

---

## After v0.6: extensions

Installed only by the people who need them (VS Code-style):

- **Formats:** OCR for scanned PDFs; Word, PowerPoint, Excel, EPUB.
- **Subjects:** mathematics (formulas), chemistry (formulas, periodic
  table), engineering (tables, unit conversion) — each with tools the AI
  can call so results are calculated, not guessed.
- **Output:** styled flashcards, formatted summaries and reports.

## Ideas beyond 1.0

Mobile companion, plugin marketplace, optional cloud sync, collaboration,
knowledge graph. Deliberately out of scope until after 1.0.
