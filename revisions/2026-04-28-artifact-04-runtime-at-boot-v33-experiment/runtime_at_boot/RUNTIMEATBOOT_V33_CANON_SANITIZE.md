# RuntimeAtBoot v33 Canon Sanitize

Date: 2026-04-27 local / 2026-04-28 UTC

Status: `canon_payload_ready_for_kaggle_push`

## Active Payload

`N:\Research\runtimeatbootdataset` is now the active Runtime-at-Boot v33 canon dataset root and is the root to publish to Kaggle.

## Architecture Boundary

The dataset now follows the established Runtime-at-Boot layout under `boot/<role>/` with canonical filenames. Study and certification are intentionally separate lanes:

- Study files: answer-key-free boot memory rows.
- Certification files: answer-bearing MCQ boot-gate rows.

This split is the contamination boundary. Certification answer keys certify memory loading; they are not solve-time memory.

## Canonical Counts

- Athena: 100 study, 100 certification.
- Aria: 100 study, 100 certification.
- Artemis: 100 study, 100 certification.
- Total: 300 study rows and 300 certification rows.

All certification files are balanced at 25 A / 25 B / 25 C / 25 D.

## Payload Hygiene

The active payload root no longer includes prior staging duplicate NDJSONs, role staging audits, `__pycache__/`, or the stale Apr 22 rebuild helper. `canondatabase/` and `test/` are retained as non-boot ancillary material and are not part of ordinary boot-study memory injection.

## Verification Artifacts

- `runtimeatbootdataset/runtimeatboot_manifest.json`
- `runtimeatbootdataset/SANITIZED_BOOT_MEMORY_BOUNDARY.json`
- `runtimeatbootdataset/V33_ROLE_FILE_AUDIT.csv`
- `runtimeatbootdataset/V33_SANITIZE_REPORT.md`
- `runtimeatbootdataset/SHA256SUMS.txt`