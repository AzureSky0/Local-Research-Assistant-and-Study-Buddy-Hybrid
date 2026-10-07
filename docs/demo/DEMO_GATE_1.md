# Loci — Demo Gate 1: try the document workflow

Thanks for testing! This takes about **20–30 minutes**. We want to know
whether adding, organizing and finding things in your documents feels
easy — so please use **your own documents** (lecture notes, papers, a
textbook PDF…), ideally 10 or more.

There are no wrong answers. If something is confusing, that is exactly
what we need to hear.

> Asking questions to an AI about your documents is **not** in this
> version yet — it comes next. This round is only about documents and search.

---

## 1. Set up (about 5 minutes)

You need Windows 10 or 11 and about 1 GB of free disk space. No Python or
other software is needed.

1. Download **Loci-0.3.0-windows.zip** from the
   [Releases page](https://github.com/AzureSky0/Local-Research-Assistant-and-Study-Buddy-Hybrid/releases) (about 120 MB).
2. Right-click the zip → **Extract All…**, and choose a folder you will
   find again (for example Documents).
3. Open the extracted **Loci** folder and double-click **Loci.exe**.
4. Windows may say *"Windows protected your PC"* because the app is not
   signed yet. Click **More info** → **Run anyway**.

The first start downloads a small search model (about 90 MB) in the
background, so be online the first time; you can carry on while it does.
After that the app works offline.

To remove the app later, delete the Loci folder and
`%LOCALAPPDATA%\Loci` (your workspaces and copies of documents).

Your documents stay on your computer. Nothing is uploaded.

---

## 2. Things to try

Try each one **without help first** — please don't read ahead for hints.
Note anything that made you stop and think.

1. **Make a place for your documents.** Create a workspace for one
   subject or project.
2. **Add your documents.** Add a few files, then a whole folder.
3. **Add a file twice.** Try adding one of the same files again.
4. **Keep working.** While documents are still being read, look around
   the app. Can you tell what it is doing and how long it will take?
5. **Find something you know is there.** Search for a word or term you
   know appears in one of your documents.
6. **Find something by describing it.** Search for an idea in your own
   words — not the exact wording used in the document.
7. **Search for nonsense.** Type something unrelated to your documents.
8. **Go to the source.** Open a result at the page where it was found.
9. **Make a second workspace.** Create another one for a different
   subject and switch between the two.
10. **Check on the app.** Find out how busy your computer is and pause
    the background work, then resume it.

---

## 3. Your feedback

Please answer briefly — a few words each is plenty.

**Rate 1 (hard) – 5 (easy):**

| | 1–5 |
|---|---|
| Adding documents was easy | |
| Organizing documents into workspaces made sense | |
| Search found what I was looking for | |
| Search felt fast | |
| I understood what the app was doing in the background | |
| I could use the app without anyone explaining it | |

**In your own words:**

1. What was the most confusing moment?
2. Was there a search that gave the wrong or no results? What did you type?
3. Did anything feel slow? When?
4. What did you expect to be able to do that you couldn't?
5. Would you use this for your own studies or research? Why / why not?
6. About your setup: how many documents did you add, and roughly how
   much RAM does your computer have?

If something crashed or looked broken, a screenshot helps a lot. Logs
are in `%LOCALAPPDATA%\Loci\logs` if you are happy to
share them.

---

## For the person running the demo

**Watch, don't help.** The questions this gate answers (ROADMAP, Demo
Gate 1):

- Is document import intuitive?
- Is workspace organization clear?
- Is searching fast enough?
- Can new users understand the workflow?

For each tester, note:

- Where they hesitated for more than a few seconds, and what they tried.
- Tasks they could not finish without help (and what help was needed).
- Exact search text for any search with surprising results.
- Number of documents, document types, and computer RAM.

**Done when** at least 3–5 people have tried it. Then: group the
feedback into "fix before v0.4" and "later", fix the first group,
merge the feature branches into `main`, and start v0.4 (Ask).
