# Artificial Evaluation Network (AEN) Paper

This GitHub staging folder is aligned to the Zenodo preprint release:

`v1.0-preprint-2026-04-22`

The `paper/` directory is an exact extraction of the Zenodo source archive
`aen_preprint_zenodo_source_20260422.zip`. It intentionally does not include
later local edits.

## Layout

- `paper/` - Zenodo source archive contents, extracted byte-for-byte.
- `artifacts/AEN_preprint_20260422.pdf` - Zenodo PDF artifact.
- `MANIFEST.json` - provenance, source hashes, and file inventory.
- `SHA256SUMS.txt` - checksums for staged files.

## Build

From the repository root:

```powershell
.\build.ps1
```

The build script runs `latexmk` from `paper/` when available, with a fallback to
`pdflatex`, `bibtex`, `pdflatex`, `pdflatex`.

## Collaboration

Use branches and pull requests for proposed changes. If the paper source changes,
tag a new version rather than modifying this Zenodo-aligned staging release in
place.
