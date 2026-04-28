# April 27 Revision Changelog

## From Frozen Canon To April 27

| layer | frozen canon | April 27 revision |
| --- | --- | --- |
| Benchmark evidence | frozen AIME reference run, 15/30 | current 0.2.3 archive, 21/30; unrestricted paper reference remains 22/30 |
| Controller shape | earlier pruned/closed-book control path | Canon-route prompting, peer section contracts, simple arbitration diagnostics |
| RuntimeAtBoot | certification-centered boot path | v32 class-strengthening rows, rich certification contracts, explicit study-row injection requirement |
| Failure taxonomy | mostly outcome tables | image-vs-witness, conditional ledger, endpoint recurrence, geometry closure, exact-cover completeness, closeout governance |
| Reproducibility posture | Zenodo paper source package | revision folder with visuals, tables, staged RuntimeAtBoot payload, extracted cells, offline instructions, and an explicit claim ladder |

## Patch-Level Correction Included Here

- `CB08_RUNTIME_REVISION = 2026-04-27-cb08-runtimeatboot-controller-section-wrapper-v1.4.9-clean-information-ack`
- `CB11_5_ARCHITECTURE_CERTIFICATE_REVISION = 2026-04-27-cb11_5-boot-memory-preserving-boundary-reset-r4`
- CB12 remains `2026-04-25-cb12-generic-hf-explicit-row-contract-r1`; no CB13 change is required for this revision.

## Why The r4 Controller Reset Wrapper Matters

The old architecture certificate could reset role sessions at problem boundaries and still report success even when no CB8 boot-memory baseline was present. r4 makes boot memory preservation a hard gate whenever RuntimeAtBoot has passed: each role must have a captured baseline and must restore it after before/after-problem resets.

## Documentation Tightening

- Added `STORY.md` to separate archived 21/30 performance, token compression, YAML study rows, RuntimeAtBoot v32 certification, and the still-pending corrected full run.
- Added `assets/evidence_pipeline/claim_ladder.svg` as a compact visual boundary marker for the same claim ladder.

## CB11.5 r4 Correction

- Added the executable r4 wrapper for `_reset_sessions_for_new_question`, because the live controller reset happened after the r3 outer restore.
- Added `cb11_5_controller_reset_boot_memory_restore` as a required certificate event for valid RuntimeAtBoot transfer reruns.
