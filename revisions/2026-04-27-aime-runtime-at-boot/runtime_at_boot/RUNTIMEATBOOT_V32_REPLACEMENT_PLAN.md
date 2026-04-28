# RuntimeAtBoot V32 Replacement Plan

Date: 2026-04-27

Status: staged replacement payload. The live `runtimeatbootdataset` folder was not mutated.

## Replacement Root

- Staged dataset root: `N:\Research\Updates_to_AEN\runtimeatboot_v32_stage_20260427\runtimeatbootdataset`
- Replacement target when publishing: the RuntimeAtBoot dataset payload root.

## What Changed

- Prepended six v32 study rows per role: five problem-class artifacts plus one controller closeout overlay.
- Prepended six v32 certification rows per role.
- Added a formal RuntimeAtBoot v32 contract document for the expected memory-injection and certification semantics.
- Updated staged `runtimeatboot_manifest.json` counts and notebook contract.
- Updated staged `SANITIZED_BOOT_MEMORY_BOUNDARY.json` to mark v32 overlay and keep certification answer keys separated.
- Added v32 certification harness audit files covering row richness, answer-position balance, and anti-answer-track constraints.
- Excluded v33 memory-shard probes; those belong to the later memory test run.

## Counts

| role | study base | v32 study | staged study | cert base | v32 cert | staged cert |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| athena | 100 | 6 | 106 | 200 | 6 | 206 |
| aria | 95 | 6 | 101 | 190 | 6 | 196 |
| artemis | 95 | 6 | 101 | 190 | 6 | 196 |

## Publish Notes

- For v32 class-strengthening tests, certify at least the first 6 lines per role, or configure the notebook to select v32 rows by priority.
- For v32 live solving, inject study rows into prompt/context. Do not inject certification answer keys into solve prompts.
- Treat certification as a RuntimeAtBoot reading gate: the MCQ answer is deliberately easy, but the row must carry a rich invariant/rubric payload and the answer letters must be balanced enough to rule out fixed-letter passing.
- Interpret the best-world target as targeted studying from injected class artifacts, not plain recall.
- For v33 memory testing, build a separate dataset with memory shards and recall probes.

## Next Dataset Intake

See NEXT_DATASET_NOTES_V33.md for the notes-only v33 curation intake. The active v32 replacement payload remains unchanged here.
## Supersession Note: v33 Canon Payload

After the v32 staged replacement work, the Apr 27 distinct all-role Runtime-at-Boot work was promoted into the active v33 canon dataset root at `N:\Research\runtimeatbootdataset`. See `NEXT_DATASET_NOTES_V33.md` and `RUNTIMEATBOOT_V33_CANON_SANITIZE.md`.