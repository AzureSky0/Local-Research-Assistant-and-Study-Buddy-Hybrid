# Third-party notices

Loci uses the open-source components listed below. The Windows package
includes them; their full licence texts are included in the package as
`THIRD_PARTY_LICENSES.txt`. Each component remains under its own licence.

## Components included in the Windows package

| Component | Licence | Used for |
|---|---|---|
| Python 3.12 | Python Software Foundation License | Runtime |
| Qt 6 via PySide6 and shiboken6 | LGPL-3.0 | User interface (the Qt libraries are separate files in the package and can be replaced) |
| PyMuPDF / MuPDF | AGPL-3.0 | Reading PDF files |
| SQLite | Public domain | Database |
| SQLAlchemy | MIT | Database access |
| Alembic | MIT | Database migrations |
| Mako | MIT | Used by Alembic |
| MarkupSafe | BSD-3-Clause | Used by Mako |
| greenlet | MIT and PSF-2.0 | Used by SQLAlchemy |
| sqlite-vec | MIT or Apache-2.0 | Vector search |
| fastembed | Apache-2.0 | Running the search model |
| ONNX Runtime | MIT | Running the search model |
| tokenizers | Apache-2.0 | Splitting text for the search model |
| py_rust_stemmers | MIT | Used by fastembed |
| mmh3 | MIT | Used by fastembed |
| huggingface_hub, hf_xet | Apache-2.0 | Downloading the search model |
| httpx, httpcore | BSD-3-Clause | Network access for the model download |
| h11, anyio | MIT | Used by httpx |
| idna | BSD-3-Clause | Used by httpx |
| certifi | MPL-2.0 | Trusted certificates for the model download (unmodified) |
| requests | Apache-2.0 | Used by dependencies |
| NumPy | BSD-3-Clause (with bundled MIT, 0BSD, Zlib, CC0 parts) | Numerical work |
| Pillow | MIT-CMU | Images |
| psutil | BSD-3-Clause | Memory and CPU readings |
| platformdirs | MIT | Finding the data folder |
| pydantic, pydantic-core, pydantic-settings, annotated-types | MIT | Settings |
| typing_extensions | PSF-2.0 | Type support |
| tqdm | MPL-2.0 and MIT | Progress reporting in dependencies (unmodified) |
| loguru | MIT | Logging in dependencies |
| PyYAML, filelock | MIT | Used by dependencies |
| fsspec, colorama | BSD-3-Clause / BSD | Used by dependencies |

## Downloaded at first use (not included)

| Model | Licence | Used for |
|---|---|---|
| snowflake/snowflake-arctic-embed-xs | Apache-2.0 | Search by meaning (Standard profile) |
| minishlab/potion-retrieval-32M | MIT | Search by meaning (Light profile) |

## Source code

Loci's complete source code is available at
https://github.com/AzureSky0/Local-Research-Assistant-and-Study-Buddy-Hybrid
(each release is tagged, for example `v0.3.1`). The source code of the
third-party components is available from their projects.

Licences as stated in each package's metadata on 2026-10-21. If you notice
an error, please open an issue.
