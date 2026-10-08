# Development guide

How to set up the code, make a change and get it merged.

## Set up

Requirements: Windows 10/11 (macOS/Linux work for development but are
not packaged), **Python 3.12**, git.

```powershell
git clone https://github.com/AzureSky0/Local-Research-Assistant-and-Study-Buddy-Hybrid.git
cd Local-Research-Assistant-and-Study-Buddy-Hybrid
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m main
```

**Use a separate data folder while developing** so you never touch your
real workspaces:

```powershell
$env:LOCI_DATA_DIR = "D:\loci-dev-data"
python -m main
```

For detailed logs, create a `.env` file in the project folder with
`DEBUG=true`. Logs are in `<data folder>\logs\app.log`.

## Daily commands

```powershell
pytest                 # all tests; UI tests run headless (offscreen)
ruff check app tests   # lint
mypy app               # type check
python -m main         # run the app
```

All three checks must pass before a pull request is merged. The tests
always use a temporary data folder.

## Branches and pull requests

- `main` is always releasable. **Never commit directly to `main`.**
- Branch names: `feature/<short-name>`, `fix/<short-name>`,
  `docs/<short-name>`, `refactor/<short-name>`, `perf/<short-name>`.
- Keep a branch focused on one change; open a pull request early if you
  want feedback.
- During a **Demo Gate**, only fixes from tester feedback are merged.
- Merge with fast-forward or squash; delete the branch afterwards.

### Commit messages

Conventional style, written for a reader who was not there:

```text
fix: show search results only when the pages support the search

Search by meaning always returns nearest neighbours, so random text
listed every document. A page now counts as evidence only when …
```

Prefixes: `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `chore`.
The subject says what changes for the user or developer; the body
explains why.

### Pull request checklist

- [ ] Tests added or updated for the change; `pytest`, `ruff`, `mypy` pass.
- [ ] Database change? A new Alembic migration, tested on a copy of real data.
- [ ] UI change? Screenshot in the pull request; wording checked (see below).
- [ ] Decision made? Added to [DECISIONS.md](DECISIONS.md).
- [ ] [STATUS.md](STATUS.md) updated if the change finishes or adds work.
- [ ] Tested in the running app, not only in tests.

## Code conventions

- **Layers** (see [ARCHITECTURE.md](ARCHITECTURE.md)): UI → Managers →
  Services → Repositories. UI never talks to the database; repositories
  never commit — services own transactions.
- **Feature folders** (`documents/`, `knowledge/`, `workspace/`, …) each
  use `domain/ dto/ mapper/ orm/ repository/ services/`.
- **Background work** goes through `AsyncTaskExecutor` and a manager;
  worker threads never touch widgets — they emit signals that are
  delivered on the UI thread.
- **Long work must be cancellable and resumable** (check `is_cancelled`,
  record progress in the database).
- Type hints everywhere (`mypy` runs on `app/`); line length 100.
- Comments explain *why*, not *what*; match the density of the code
  around you.
- Name things for what they mean to the user (`documents_to_read`, not
  `queue_len`).

## Writing for users (UI text)

- Audience-neutral: "documents", not "study material"; no assumption that
  the user is a student.
- Plain words: "search by meaning", not "semantic vector retrieval".
- Say what happens and what to do: "Search by meaning is unavailable —
  word search still works."
- Never blame the user; never show a raw error or stack trace.

## Database changes

1. Change the ORM model.
2. `alembic revision --autogenerate -m "short description"` and **read the
   generated file** — autogenerate misses things.
3. SQLite needs batch mode for most changes (`render_as_batch` is on).
   Foreign keys are switched off during migrations so table rebuilds do
   not cascade-delete rows; the integrity check runs afterwards.
4. Rebuilding a table drops its triggers: re-create them in the migration.
5. Test the migration on a **copy** of a real data folder.
6. New migration imports are picked up by the Windows build
   automatically (`packaging/loci.spec`).

The app runs migrations automatically on start-up.

## Debugging tips

- Logs: `<data folder>\logs\app.log`; unexpected errors are always
  logged there, also in the packaged app.
- Database: `<data folder>\database\local_research.db` — open a **copy**
  with any SQLite browser (the app uses WAL mode and the sqlite-vec
  extension).
- Background work can be paused from the status indicator — handy when
  reproducing timing problems.
- Search quality questions: use the benchmark (see
  [TESTING_AND_QUALITY.md](TESTING_AND_QUALITY.md)) rather than a single
  example.
