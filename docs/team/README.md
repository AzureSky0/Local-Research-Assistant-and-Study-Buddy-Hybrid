# Team handbook

Everything the development team needs to understand, build and ship
**Loci** (working name), the local knowledge bank.

Last reviewed: 2026-10-08 · Owner: Akshat Sahu (project lead)

## Start here

| If you want to… | Read |
|---|---|
| Understand what we are building and why | [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) |
| Know where we are right now and what is next | [STATUS.md](STATUS.md) |
| See the whole plan, version by version | [ROADMAP.md](ROADMAP.md) |
| Present the project in a meeting | [meetings/2026-10-08-project-update.md](meetings/2026-10-08-project-update.md) |
| Set up the code and start contributing | [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) |
| Understand how the app is built | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Know why things are the way they are | [DECISIONS.md](DECISIONS.md) |
| Test changes and judge quality | [TESTING_AND_QUALITY.md](TESTING_AND_QUALITY.md) |
| Build and publish a release | [RELEASE_PROCESS.md](RELEASE_PROCESS.md) |
| Record tester feedback from Demo Gate 1 | [FEEDBACK_LOG.md](FEEDBACK_LOG.md) |
| Look up a term | [GLOSSARY.md](GLOSSARY.md) |
| Take notes in a meeting | [meetings/TEMPLATE.md](meetings/TEMPLATE.md) |

## New to the team? Your first week

1. Read the overview, status and roadmap (about 30 minutes).
2. Install the app from the [latest release](https://github.com/AzureSky0/Local-Research-Assistant-and-Study-Buddy-Hybrid/releases)
   and do the tester tasks in [../demo/DEMO_GATE_1.md](../demo/DEMO_GATE_1.md) —
   you will understand the product faster as a user first.
3. Set up the code with the [development guide](DEVELOPMENT_GUIDE.md) and run the tests.
4. Read the [architecture](ARCHITECTURE.md), then follow one search from the
   search box to the database in the code.
5. Pick a small item from "Known issues" in [STATUS.md](STATUS.md) and open a
   pull request.

## Keeping these documents useful

- **STATUS.md** is updated at least once a week and after every release.
- **Meeting notes** go in `meetings/` as `YYYY-MM-DD-topic.md`, from the template.
- **New decisions** are added to [DECISIONS.md](DECISIONS.md) in the same pull
  request as the change they explain.
- If a document is wrong, fix it in your next pull request — out-of-date docs
  are worse than none.

The full product requirements (PRD), detailed roadmap and full decision log
are kept by the project lead in `docs/project_helper/` (not in the
repository). The documents here summarize what the team needs from them.
