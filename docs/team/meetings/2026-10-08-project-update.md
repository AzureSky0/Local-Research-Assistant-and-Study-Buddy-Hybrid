# Project update — Loci (working name)

**Date:** 2026-10-08 · **Presenter:** Akshat Sahu · **Length:** 30 minutes
**Audience:** team members, mentors and prospective testers

## Agenda

| Time | Item |
|---|---|
| 0–3 min | What Loci is and why |
| 3–13 min | Live demo |
| 13–18 min | Where we are: progress and numbers |
| 18–23 min | What is next |
| 23–30 min | What we need from you · questions |

---

## 1. What Loci is (3 min)

> Loci is a desktop app that turns your pile of PDFs, books and notes
> into a private knowledge bank on your own computer. You import once,
> then find anything by words or by meaning and jump straight to the
> page. Next, it will answer questions from your documents — with every
> claim cited to a page you can check. Nothing is uploaded anywhere.

Why it matters:

- Students and researchers re-upload the same documents to online AI
  tools, with no memory and real privacy concerns.
- AI answers are hard to trust when you cannot see the source.
- Ordinary laptops are now strong enough to do this locally.

## 2. Live demo (10 min)

**Prepare before the meeting:** install the
[v0.3.0 release](https://github.com/AzureSky0/Local-Research-Assistant-and-Study-Buddy-Hybrid/releases/tag/v0.3.0)
and open it once (so the search model is downloaded); have a folder of
10–20 PDFs ready, ideally on a topic the audience knows; close other
heavy apps.

| Step | Do | Say |
|---|---|---|
| 1 | Create a workspace, e.g. "Machine learning papers" | "One workspace per subject or project." |
| 2 | Add the whole folder | "Small files first; you can work while it reads. Note the time-left estimate at the bottom right." |
| 3 | Click the status indicator | "It shows what's running, time left, and how busy the computer is — and pauses itself if memory runs low." |
| 4 | Search an exact term, e.g. `dropout` | "Word search is instant, with the page and the matching passage." |
| 5 | Search an idea in other words, e.g. `stopping a network from memorising the training data` | "Search by meaning finds passages that say it differently." |
| 6 | Search nonsense, e.g. `my grandmother bakes chocolate cake` | "If nothing really matches, it says so — no made-up results." |
| 7 | Open a result at its page | "Straight to the page in your PDF viewer." |
| 8 | Add the same file again | "Duplicates are detected." |

If something goes wrong: stay calm, say it is a test version, and note it
in [../FEEDBACK_LOG.md](../FEEDBACK_LOG.md) — that is exactly what Demo
Gate 1 is for.

## 3. Where we are (5 min)

```text
v0.1 ✅ ── v0.2 ✅ ── v0.3 ✅ ── 🚧 Demo Gate 1 (now) ── v0.4 AI Assistant ── v0.5 Prototype ── 🚧 Demo Gate 2
```

- **Done:** workspaces, import, background reading, search by words and
  meaning, open at page, status and pause, Windows app (no Python
  needed).
- **Measured on 358 research papers (~10,000 pages):**
  - right paper in the top 5 results for **87%** of 45 test questions
    (100% for direct questions, 67% for hard paraphrased ones);
  - a typical PDF is searchable in a fraction of a second;
  - all 358 papers fully searchable by meaning in about 30 minutes, in
    the background, on a normal 16 GB laptop;
  - searches answer in well under a tenth of a second.
- **Quality:** 256 automated tests; every model and storage choice made
  by benchmark.

## 4. What is next (5 min)

1. **Demo Gate 1 (now):** 3–5 people try the app with their own
   documents; we fix what confuses them.
2. **v0.4 AI Assistant:** an *Ask* section — answers only from your
   documents, each claim checked against its source, cited to the page.
   First we benchmark local AI models to see what runs well on ordinary
   laptops.
3. **v0.5 First public prototype**, then Demo Gate 2.

Later: study tools (flashcards, quizzes, exam-paper analysis), then
optional extensions (OCR for scanned PDFs, maths and chemistry support,
more file types).

## 5. What we need from you (7 min)

- **Testers:** 20–30 minutes with your own documents, using the
  [tester guide](../../demo/DEMO_GATE_1.md). Windows 10/11 needed for now.
- **Names:** "Loci" is a working name (many names are taken) —
  suggestions welcome.
- **Documents you rely on:** what types do you use most (scanned PDFs?
  Word? slides?) — this shapes the extension order.

### Likely questions

| Question | Answer |
|---|---|
| Does it send my documents anywhere? | No. Everything runs on your computer. The only download is the search model, once. |
| Mac or Linux? | The code runs there, but we only package for Windows so far. |
| Why not just use ChatGPT? | Your documents stay private, it remembers your whole collection, and every answer will point to the page so you can check it. |
| Which AI model will it use? | A local model chosen by benchmark in v0.4, sized to the computer (8 GB vs 16 GB laptops). |
| Scanned PDFs? | Not yet — OCR comes as an extension later. |
| What does it cost? | Nothing; it is a learning project for now. |

## Notes and actions (fill in during the meeting)

| Action | Owner | Due |
|---|---|---|
| | | |
