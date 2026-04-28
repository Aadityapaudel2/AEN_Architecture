# Next RuntimeAtBoot Dataset Notes: v33 Curation Intake

Status: `notes_only_not_promoted`

This note records the next RuntimeAtBoot dataset candidate after the April 27 v32 package. It does not replace the committed v32 payload and does not claim a finalized v33 dataset.

## Local Intake Folder

```text
N:\Research\Updates_to_AEN\bootupdates\to_be_staged\runtimeatboot_v33_curation_20260428
```

## What Changed Locally

A direct search under `N:\Research` found no literal finalized `runtimeatboot_v33` dataset folder. The ready-to-curate material is a v33 intake folder built from the strongest available candidate:

```text
N:\Research\Updates_to_AEN\bootupdates\to_be_staged\runtimeatboot_v321_distinct_100_all_roles_20260427
```

The intake also includes reference audits from:

```text
N:\Research\Updates_to_AEN\bootupdates\to_be_staged\sharpened_cert_datasets_20260427
N:\Research\Updates_to_AEN\bootupdates\to_be_staged\cert_buff_linewise_swarm_20260427
```

## Verification Snapshot

The intake checksum ledger verifies, and the copied source candidate matches the original source candidate byte-for-byte.

`ROLE_FILE_AUDIT.csv` reports:

| role | study rows | cert rows | bad JSON | cert answer balance |
| --- | ---: | ---: | ---: | --- |
| Athena | 100 | 100 | 0 | 25 A / 25 B / 25 C / 25 D |
| Aria | 100 | 100 | 0 | 25 A / 25 B / 25 C / 25 D |
| Artemis | 100 | 100 | 0 | 25 A / 25 B / 25 C / 25 D |

Study rows have no answer-letter fields in the quick audit.

## Curation Boundary

The v32 replacement plan explicitly says v33 should be the memory-shard / recall-probe stage. The v32.1 distinct 100 all-role package is clean and balanced, but it should not be promoted as final v33 until one of these decisions is made:

1. Add memory-shard and recall-probe rows.
2. Rename the candidate as a distinctness-only v32.1/v32.2 continuation.
3. Explicitly accept the 100-distinct all-role package as v33 and defer memory-shard probes.

## Suggested Next Action

Curate inside:

```text
N:\Research\Updates_to_AEN\bootupdates\to_be_staged\runtimeatboot_v33_curation_20260428\curation_workspace
```

Only move files into `promote_ready/` after the checklist clears study/cert separation, forbidden terms, answer balance, and the v33 memory-shard policy.