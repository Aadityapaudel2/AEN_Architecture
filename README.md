# Artificial Evaluation Network (AEN) Paper

This GitHub staging folder is aligned to the Zenodo preprint release:

`v1.0-preprint-2026-04-22`

The `paper/` directory is an exact extraction of the Zenodo source archive
`aen_preprint_zenodo_source_20260422.zip`. It intentionally does not include
later local edits.

## Layout

- `paper/` - Zenodo source archive contents, extracted byte-for-byte.
- `artifacts/AEN_RAB_source_snapshot.pdf` - Zenodo PDF artifact.
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


## Repository Guide

| entry point | purpose |
| --- | --- |
| [`NAVIGATION.md`](NAVIGATION.md) | readable map of the paper, revision package, data, and Pages preview |
| [`docs/`](docs/) | GitHub Pages source folder; enable Pages from `main` / `docs` in repository settings |
| [`revisions/`](revisions/) | dated artifact ledger for the AIME Q1-Q30 revision runs |

## Revision Artifacts

The follow-on AIME evidence lives under [`revisions/`](revisions/). The folder is
organized as dated artifacts rather than mutable labels:

- Artifact 01: frozen pruned baseline.
- Artifact 02: unrestricted reference.
- Artifact 03: April 27 benchmarkgrade v0.2.3 run.
- Artifact 04: April 28 RuntimeAtBoot v33 experiment.

The frozen Zenodo paper source remains unchanged.
