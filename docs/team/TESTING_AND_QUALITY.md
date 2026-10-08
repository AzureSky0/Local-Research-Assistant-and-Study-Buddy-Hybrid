# Testing and quality

Three layers: automated tests on every change, the search benchmark for
anything that affects search or speed, and real users at Demo Gates.

## 1. Automated tests (every change)

```powershell
pytest                 # about 260 tests, about 10 seconds
ruff check app tests
mypy app
```

- Tests mirror `app/` (`tests/documents`, `tests/knowledge`, `tests/ui`, …).
- Database tests use an in-memory SQLite database with the same
  settings as the app (FTS5, sqlite-vec, foreign keys).
- **Search by meaning is tested with a fake embedder**
  (`tests/knowledge/fake_embedder.py`): instant, no download, with a small
  synonym table so "meaning" can be tested.
- **UI tests** run headless (`QT_QPA_PLATFORM=offscreen`) and drive real
  pages and managers.
- Tests never touch the real data folder (`tests/conftest.py` points it
  at a temporary folder).

What to test with a change:

| Change | Add |
|---|---|
| A bug fix | A test that fails without the fix |
| A service or repository | Tests of its behaviour, including empty and error cases |
| A UI flow | A UI test that clicks through it |
| A migration | A test on data shaped like the previous schema, or a manual run on a copy of real data |
| Search ranking | A test for the case **and** a benchmark run |

## 2. Search benchmark (search, models, speed)

`scripts/benchmark/` holds a reproducible benchmark: **358 openly
licensed arXiv papers** and **45 questions** (25 direct, 5 student-style,
15 hard paraphrases), each with the paper that answers it.

```powershell
# once: download the papers into data/benchmark/arxiv
python scripts/benchmark/download_arxiv_corpus.py

# import + reading + keyword search (creates a benchmark database)
python scripts/benchmark/benchmark_pipeline.py data/benchmark/arxiv data/benchmark/results

# search by meaning and hybrid, for one model (add --stores to compare vector stores)
python scripts/benchmark/benchmark_embeddings.py `
  data/benchmark/results/data/database/local_research.db data/benchmark/results `
  --backend fastembed --model snowflake/snowflake-arctic-embed-xs
```

A full embedding run takes about 30 minutes on a 16 GB laptop. Results
go to `data/benchmark/` (not committed). Current baseline:

| Measure | Baseline |
|---|---|
| Correct paper in top 5, hybrid | 87% (hard questions 67%) |
| Correct paper first, hybrid | 71% |
| Keyword search | < 100 ms |
| Vector lookup (sqlite-vec) | ~33 ms median |
| Reading per PDF | 0.14 s median, 2.0 s 95th percentile |
| Embedding speed (arctic-embed-xs, CPU) | ~12 passages/s |

Rules:

- A change that touches search must **not lower** top-5 accuracy, and
  must keep latency within the targets in [DECISIONS.md](DECISIONS.md) (034).
- With 45 questions, one or two questions of difference is noise; look
  for consistent changes.
- Also check that **unrelated searches find nothing** (for example
  "my grandmother bakes chocolate cake").

## 3. Manual checks before a release

- [ ] Fresh data folder: start, import a folder of PDFs, watch the status
      indicator to "All caught up".
- [ ] Search by words, by meaning, and nonsense text.
- [ ] Open a result at its page.
- [ ] Pause and resume background work.
- [ ] Restart the app during reading: it continues where it stopped.
- [ ] The packaged app on a computer (or folder) **without Python**
      (see [RELEASE_PROCESS.md](RELEASE_PROCESS.md)).
- [ ] The log has no errors.

## 4. Real users (Demo Gates)

At each Demo Gate, 3–5 people outside the team use the app with their own
documents, following a tester guide, while someone watches without
helping. Feedback goes into [FEEDBACK_LOG.md](FEEDBACK_LOG.md).
The current guide: [../demo/DEMO_GATE_1.md](../demo/DEMO_GATE_1.md).
