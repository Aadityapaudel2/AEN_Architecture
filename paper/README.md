# Runtime-at-Boot and Triadic Inference Paper Draft

This directory contains a first-draft LaTeX preprint for the AEN/Athena inference-time mathematical reasoning architecture.

The draft intentionally defers detailed retrospective analysis. It focuses on architecture, Runtime-at-Boot certification, triadic reasoning roles, controller-owned finalization, evaluation methodology, AIMO3 deployment framing, larger-resource plans, limitations, and reproducibility.

## Files

- `main.tex` - paper draft.
- `references.bib` - BibTeX for the single local scholarly citation used in this draft.
- `diagrams/aen_architecture.tex` - LaTeX/TikZ architecture diagram included by `main.tex`; it combines Runtime-at-Boot memory/certification with the solve-time role protocol.
- `diagrams/triadic_turn_protocol.tex` - generated LaTeX/TikZ budgeted triadic controller-loop diagram.
- `diagrams/*.pdf` and `diagrams/*.png` - rendered diagram files for direct viewing.
- `diagrams/render_diagrams.ps1` - helper to regenerate rendered diagrams.
- `build.ps1` - local build helper.

## Build

From this directory:

```powershell
.\build.ps1
```

The script uses `latexmk` if available. Otherwise it falls back to:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

## Evidence Policy

Every empirical claim in the draft should be tied to one of these categories:

- A local artifact path, such as a JSON audit, CSV log, README, notebook manifest, or source file.
- A planned or pending experiment, clearly marked as not yet a result.

The draft should not present AIMO3 deployment metadata or local smoke tests as an external benchmark score. AIMO3 is used here as a constrained-deployment motivation and reproducibility context.

## Main Evidence Sources

- `research/`
- `kaggle_aimo3/`
- `kaggle_push/kernel-metadata.json`
- `kaggle_push/AENAIMO19_READINESS_AUDIT.json`
- `kaggle_aimo3/AENAIMO19/README.md`
- `apps/two_model_dialogue_evaluator/`
- `Finetune/`
- `kaggle_aimo3/context_runtime/`
- `kaggle_aimo3/context_runtime/refined/publication_audit/`
- `kaggle_aimo3/turndiscipline/researchnotes/`
- `kaggle_aimo3/turndiscipline/README_PAPER_DIAGRAM.md`
- `kaggle_aimo3/research_3bodylocal/`
- `research/AIMO3_QWEN9B_PHI15B_*`
- `research/3bodyalgorithm_study.md`
- `research/AIMOAEN11_RUNTIME_STABILIZATION_2026_04_02.md`

## Updating Results

When adding a result, include:

- Artifact path.
- Dataset status: external, attached, internal, local structural, or planned.
- Model/runtime configuration.
- Whether Runtime-at-Boot passed.
- Whether the answer was verified, unverified, or emitted through another explicit finalization mode.

Do not add retrospective analysis tables or detailed historical-debugging narrative to this draft unless the project intentionally starts a new revision that includes that material.

## Citation Policy

Do not add outside citations unless the corresponding source has been deliberately inspected and accepted for this paper. The current draft uses only the local Simon Frieder et al. paper from `kaggle_aimo3/papers/2412.15184v2.pdf`. Repository artifacts should be cited inline by path rather than converted into fake bibliographic references.
