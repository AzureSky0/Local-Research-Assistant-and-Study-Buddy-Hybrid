# Glossary

Terms used in the code and these documents. In the **app itself** we use
the plain words in the "Users see" column.

| Term | Meaning | Users see |
|---|---|---|
| **Workspace** | A separate collection of documents with its own search and memory (one per subject, project or book). | Workspace |
| **Library** | The workspace page for viewing and searching documents. | Library |
| **Ask** *(v0.4)* | The workspace page for questions answered from the documents, with citations. | Ask |
| **Document** | An imported file (PDF, `.txt`, `.md`); the app keeps its own copy. | Document |
| **Page** | Extracted text of one page; text files have one page. Results and citations point to pages. | Page |
| **Chunk / passage** | A piece of a document (~220 words, overlapping by 40) used for search by meaning; records its page range. | Passage |
| **Processing pipeline** | The staged background work after import: extract → keyword index → chunk. Each stage is stored, so it resumes after a restart. | "Reading documents" |
| **Embedding** | A list of numbers (a vector) that represents a passage's meaning; similar meanings give nearby vectors. | "Preparing search by meaning" |
| **Embedding model** | The small local model that makes embeddings: arctic-embed-xs (Standard) or potion-retrieval-32M (Light). | Search model |
| **Keyword search** | Search by words with SQLite FTS5 (word forms match: "learn" finds "learning"), ranked by bm25. | Search by words |
| **Semantic search** | Search by meaning: nearest passages to the query's embedding (sqlite-vec). | Search by meaning |
| **Hybrid search** | Both searches combined with reciprocal rank fusion (RRF). | — |
| **Evidence check** | A page counts only if it contains ≥30% of the search's meaningful words; stops random text from matching. | — |
| **Stop words** | Very common words ("the", "of") ignored by search. | — |
| **FTS5** | SQLite's full-text search engine. | — |
| **sqlite-vec** | SQLite extension that stores vectors and finds the nearest ones. | — |
| **fastembed / ONNX** | Library and model format that run embedding models on the CPU without PyTorch. | — |
| **Computer profile** | Light or Standard, detected from RAM (≥ 12 GB → Standard); chooses the models. | This computer |
| **Workspace focus** *(planned)* | Look up & explain, or Study & analyze — how much background work a workspace does. | Workspace focus |
| **Background manager** | Watches the computer, shows the status indicator, estimates time left, pauses when memory is low. | Status indicator (bottom right) |
| **Capability registry** | Lookup of features by name (`document.pdf.read`) so extensions can add readers and tools. | — |
| **Extension / plugin** *(planned)* | Optional add-on: file formats, OCR, subject tools, styled outputs. | Extensions |
| **Knowledge pack** *(v0.7)* | Installable offline knowledge (dictionaries, reference data). | Knowledge packs |
| **LLM** *(v0.4)* | Large language model; runs locally to write answers. | AI model |
| **Citation** *(v0.4)* | Document and page supporting a claim in an answer; opens the page. | Source |
| **Demo Gate** | A planned pause in feature work to test with real users. | — |
| **Data folder** | Where the app keeps everything: `%LOCALAPPDATA%\Loci`. | — |
| **Migration** | An Alembic script that changes the database schema; runs at start-up. | — |
| **Benchmark** | The reproducible test with 358 arXiv papers and 45 questions used for search and model choices. | — |
