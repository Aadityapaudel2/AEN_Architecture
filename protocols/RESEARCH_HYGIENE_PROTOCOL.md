# AEN Research Hygiene Protocol

This protocol keeps AEN readable and auditable as the project accumulates notebooks, run exports, boot datasets, figures, and cross-agent logs.

## Repository Zones

| zone | meaning | rule |
| --- | --- | --- |
| `paper/` | frozen preprint source | do not mutate for new experiments |
| `artifacts/` | rendered/frozen staged artifacts | update only for deliberate releases |
| `revisions/` | living evidence ledger | every run gets a dated artifact folder |
| `experiment_plan/` | planning material | must not be mistaken for completed evidence |
| `next_run_v34/` | executable next-run package | after the run, either archive or supersede clearly |
| `runtimeatbootdataset_v34/` | answer-aware V34 boot dataset | label as contaminated/answer-aware, not clean boot data |
| `protocols/` | operating rules for future agents | keep short, explicit, and current |

## Naming Rules

Use durable names:

- Good: `2026-04-29-artifact-06-v34-full-test-run`
- Good: `v34_answer_anchor_scan.csv`
- Bad: `current`, `latest`, `official`, `final_final`, `new_run`

If a raw legacy file uses a floating name, preserve it for traceability but translate it in the README.

## Artifact Folder Minimum

Every major run artifact should contain:

- `README.md` with claim boundary,
- `MANIFEST.md` with file inventory,
- `REPRODUCIBILITY.md` when execution matters,
- `data/` with derived CSV/JSON tables,
- `visualizations/` for figures,
- `per_question_reports/` when applicable,
- `raw_export/` only when intentionally publishable,
- `scripts/` for generators,
- a note if the run is blind, answer-aware, diagnostic, or contaminated.

## Claim Boundary Labels

Use these labels consistently:

| label | use when |
| --- | --- |
| Blind benchmark | no target answers or problem-specific solution hints are available to the runtime |
| Answer-aware replay | exact answers or answer-key facts are available in context |
| Context-recall diagnostic | goal is to prove memory loading/persistence/recall, not independent solving |
| Controller diagnostic | goal is turn order, closeout, reset, or routing analysis |
| Transcript diagnostic | goal is qualitative failure analysis on selected cases |
| Planning package | proposed changes, not executed evidence |

V34 must be labeled as answer-aware replay / context-recall diagnostic, not blind benchmark.

## Data Hygiene

Before a dataset enters `runtimeatboot*` or a run artifact:

- remove secrets and personal tokens,
- record source path and creation time,
- include schema expectations,
- identify whether it is answer-aware or answer-free,
- scan studied text for exact benchmark answers,
- preserve row counts and hashes where practical,
- keep certification data separate from study data.

## External API Hygiene

External model use belongs in a clearly named local log folder, for example:

`N:\Research\CrossAgentic\codex_internal__gemini_external_logs`

Do not mix external API transcripts into AEN GitHub artifacts unless they are sanitized and intentionally cited.

## Notebook Hygiene

For notebooks:

- keep executable codeblocks synced to plain `.py` files when possible,
- avoid hidden state assumptions in durable artifacts,
- record runtime revision strings,
- record dataset source and selected rows,
- export logs after major runs,
- do not treat a notebook cell as authoritative without an exported code snapshot.

## Raw Export Hygiene

Raw exports should be copied into artifact folders only when useful and safe. If a raw export contains private or answer-bearing material, label it explicitly and keep the claim boundary honest.

## V34 Hygiene Status

V34 now has:

- full run report,
- visual index,
- per-question reports,
- context-recall correction diagnostic,
- forensic addendum,
- answer-anchor scan table,
- compute profile table,
- raw export copy,
- generator scripts.

Remaining cleanup work:

- add a V35 contamination scanner before any new long run,
- quarantine answer-aware boot datasets from clean boot datasets,
- archive or rename planning folders after their corresponding artifact exists,
- create one root "start here" route for future agents.

## Future-Agent Start Route

A new agent should read in this order:

1. [`NAVIGATION.md`](../NAVIGATION.md)
2. [`revisions/README.md`](../revisions/README.md)
3. [`revisions/2026-04-29-artifact-06-v34-full-test-run/CONTEXT_RECALL_DIAGNOSTIC.md`](../revisions/2026-04-29-artifact-06-v34-full-test-run/CONTEXT_RECALL_DIAGNOSTIC.md)
4. [`revisions/2026-04-29-artifact-06-v34-full-test-run/FORENSIC_ADDENDUM.md`](../revisions/2026-04-29-artifact-06-v34-full-test-run/FORENSIC_ADDENDUM.md)
5. [`protocols/AGENT_FREEZE_PROTOCOL.md`](AGENT_FREEZE_PROTOCOL.md)

That route gives the project state without requiring the agent to reverse-engineer it from filenames.