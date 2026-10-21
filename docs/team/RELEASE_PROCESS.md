# Release process

How to build the Windows app and publish it for testers.

## Versions

- `APP_VERSION` in `app/core/constants.py` follows the roadmap:
  `0.3.0` = v0.3. Fixes during a Demo Gate are `0.3.1`, `0.3.2`, …
- Git tags match: `v0.3.0`, `v0.3.1`.
- Releases are made from `main` only.

## Checklist

1. **Prepare**
   - [ ] Everything for the release is merged into `main`; `pytest`,
         `ruff`, `mypy` pass.
   - [ ] `APP_VERSION` updated (`app/core/constants.py`).
   - [ ] [STATUS.md](STATUS.md) changelog updated.
2. **Build**
   ```powershell
   pip install pyinstaller          # once
   python scripts/build_windows.py
   ```
   Produces `dist/Loci/Loci.exe` (~290 MB folder) and
   `dist/Loci-<version>-windows.zip` (~120 MB).
3. **Test the build** without Python on the PATH and with an empty data
   folder:
   ```powershell
   $env:LOCI_DATA_DIR = "$env:TEMP\loci-release-check"
   $env:PATH = "C:\Windows\System32;C:\Windows"
   Start-Process dist\Loci\Loci.exe
   ```
   - [ ] The window opens; create a workspace and import a few PDFs.
   - [ ] Search works by words and, after the model download, by meaning.
   - [ ] `%TEMP%\loci-release-check\logs\app.log` has no errors.
4. **Publish** (GitHub CLI, logged in with `gh auth login`):
   ```powershell
   gh release create v0.3.1 dist\Loci-0.3.1-windows.zip `
     --target main --title "Loci 0.3.1" --notes-file release-notes.md
   ```
   Release notes are written for testers: what it is, how to install
   (including "More info → Run anyway"), what is new, what to try.
5. **Verify:** download the zip from the release page and run it once.
6. **Announce** to testers with the release link.

## What the build contains

Defined in `packaging/loci.spec`, plus a `licenses` folder added by
`scripts/build_windows.py` (Loci's AGPL licence and extension exception,
third-party notices, every bundled component's licence text, and where to
get the source code). When a dependency is added, add it to
`BUNDLED_PACKAGES` in the build script and to `THIRD_PARTY_NOTICES.md`.

- The app, Python and all libraries (Qt, PyMuPDF, ONNX Runtime, NumPy).
- `alembic.ini` and the migration scripts (Alembic reads them from disk);
  the imports used by migrations are collected automatically.
- The sqlite-vec extension (`vec0.dll`).
- **Not** the search model: it downloads on first start (~90 MB) into the
  user's data folder.

The packaged app has no console: unexpected errors are written to the
log, and libraries that print to the console are silenced.

## Known limitations

- **Unsigned:** Windows SmartScreen warns "unknown publisher". A code
  signing certificate is needed before the public release.
- No installer or Start-menu entry yet: testers unzip and run.
- No automatic updates: testers download new versions from the release
  page.
- Windows only for now.

## If a release is broken

1. Mark the release as a pre-release or delete its zip on GitHub so no
   one else downloads it.
2. Fix on a `fix/` branch, merge, release the next patch version.
3. Tell testers which version to use.
