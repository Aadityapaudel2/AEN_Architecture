# RuntimeAtBoot Dataset Notes: v33 Canon Payload

Status: `promoted_to_canon_payload_ready`

This note supersedes the earlier v33 curation-intake note. The active Kaggle payload root has now been sanitized and promoted to Runtime-at-Boot canon dataset v33.

## Canon Payload Root

```text
N:\Research\runtimeatbootdataset
```

This is the exact local root intended for Kaggle dataset publication as:

```text
aadityapaudel/runtimeatboot
```

Expected notebook mount path:

```text
/kaggle/input/runtimeatboot/runtimeatbootdataset
```

## GitHub Revision Snapshot

A matching snapshot is mirrored in this revision directory:

```text
revisions/2026-04-27-aime-runtime-at-boot/runtime_at_boot/runtimeatbootdataset
```

The snapshot is documentation/provenance for the paper repo. The Kaggle push should use the active local payload root above.

## What Changed

- Promoted the Apr 27 distinct 100-slot all-role Runtime-at-Boot work into v33 canonical row identity.
- Replaced the six canonical boot filenames in-place, preserving the established `boot/<role>/...` layout.
- Removed prior staging duplicates, role staging audits, cache files, and the stale Apr 22 rebuild helper from the active payload root.
- Regenerated `runtimeatboot_manifest.json`, `SANITIZED_BOOT_MEMORY_BOUNDARY.json`, `V33_ROLE_FILE_AUDIT.csv`, `V33_SANITIZE_REPORT.md`, and `SHA256SUMS.txt`.

## Verification Snapshot

| role | study rows | cert rows | study answer rows | cert answer balance | bad JSON |
| --- | ---: | ---: | ---: | --- | ---: |
| Athena | 100 | 100 | 0 | 25 A / 25 B / 25 C / 25 D | 0 |
| Aria | 100 | 100 | 0 | 25 A / 25 B / 25 C / 25 D | 0 |
| Artemis | 100 | 100 | 0 | 25 A / 25 B / 25 C / 25 D | 0 |

`SHA256SUMS.txt` verifies against the payload files.

## Study / Certification Boundary

Study and certification remain separate by design. Study rows are answer-key-free memory rows that may become `SAFE_RUNTIME_BOOT_MEMORY`; certification rows are answer-bearing MCQ probes used only by the boot gate. The certification files must not be injected into ordinary solve prompts.

## Backup

The active local root was backed up before sanitize at:

```text
N:\Research\Updates_to_AEN\bootupdates\archives\runtimeatbootdataset_pre_v33_sanitize_20260427-214041
```

The previous GitHub revision snapshot was backed up before mirroring at:

```text
N:\Research\Updates_to_AEN\bootupdates\archives\github_runtimeatbootdataset_pre_v33_sync_20260427-214517
```