# V34 Forensic Addendum

This addendum extends the V34 full-run report with a focused forensic read of the raw transcripts and compute tables. It should be read together with [`CONTEXT_RECALL_DIAGNOSTIC.md`](CONTEXT_RECALL_DIAGNOSTIC.md).

## Bottom Line

V34 is the highest-scoring internal AEN replay artifact: **29/30 (96.67%)**, with only Q04 missed. But the transcript scan confirms the correct interpretation: V34 is a Runtime-at-Boot context-persistence and recall experiment, not a blind AIME reasoning benchmark.

The scan found answer-anchor language in **18/30** question transcripts and direct verified-answer / answer-key / ground-truth language in **17/30**. Across the run, the scanner counted **620** answer-context hits, including **181** verified-answer hits and **283** boot-record references.

## What Went Right

- CB8 loaded and preserved the Runtime-at-Boot baseline through the whole run.
- The synthetic `BOOT_CERTIFIED` path prevented the earlier boot-study generation loop.
- Per-question reset restored the after-certification baseline before each problem.
- The models could retrieve boot content explicitly, including answer anchors, many hours into the run.
- All 13 targeted prior misses were repaired in this answer-aware setting.
- The architecture produced durable logs, per-turn timings, role-token splits, and replayable transcripts.

## What Went Wrong

- The V34 boot data crossed the boundary from generalized repair guidance into exact-answer contamination.
- Direct answer-anchor language appears in the transcripts, so the headline score cannot be used as a blind benchmark claim.
- Several successful transcripts show source-priority behavior over independent derivation, which is good for memory validation but invalidates pure reasoning interpretation.
- Q04 still failed despite the answer-aware setup, showing that controller synthesis/object identification can override or miss the intended target even when the memory layer is strong.
- External-model workflow is now powerful enough to be useful, but it needs an Agent Freeze protocol before raw files are exported to any API.

## Answer-Anchor Evidence

| q | anchor_hits | verified_hits | class | targeted |
| --- | --- | --- | --- | --- |
| Q15 | 131 | 31 | direct_answer_anchor_language | True |
| Q11 | 119 | 25 | direct_answer_anchor_language | True |
| Q23 | 88 | 38 | direct_answer_anchor_language | True |
| Q29 | 65 | 11 | direct_answer_anchor_language | True |
| Q24 | 48 | 22 | direct_answer_anchor_language | True |
| Q09 | 40 | 15 | direct_answer_anchor_language | True |
| Q21 | 30 | 5 | direct_answer_anchor_language | True |
| Q17 | 26 | 18 | direct_answer_anchor_language | True |

Full table: [`data/v34_answer_anchor_scan.csv`](data/v34_answer_anchor_scan.csv).

## Compute Profile

V34 solve wall time was **11h 54m 11s**, Runtime-at-Boot wall time was **56m 37s**, and end-to-end wall time was **12h 50m 48s**. The run consumed **130,647,799** total tokens: **129,615,060** prompt tokens and **1,032,739** completion tokens.

Mean per-question token use was **4.355M** and median was **2.84M**. Mean per-question elapsed time was **23.81 minutes** and median was **18.38 minutes**.

### Highest Token Questions

| q | tokens_M | minutes | loops | turns | anchor_hits |
| --- | --- | --- | --- | --- | --- |
| Q29 | 9.107 | 56.19 | 3 | 36 | 65 |
| Q13 | 8.901 | 42.76 | 3 | 36 | 1 |
| Q04 | 8.535 | 49.5 | 3 | 34 | 11 |
| Q11 | 8.416 | 45.6 | 3 | 34 | 119 |
| Q26 | 5.904 | 35.0 | 2 | 24 | 2 |
| Q22 | 5.886 | 37.58 | 2 | 24 | 1 |
| Q23 | 5.876 | 34.37 | 2 | 24 | 88 |
| Q15 | 5.821 | 31.24 | 2 | 24 | 131 |

### Slowest Questions

| q | minutes | tokens_M | loops | turns | class |
| --- | --- | --- | --- | --- | --- |
| Q29 | 56.19 | 9.107 | 3 | 36 | direct_answer_anchor_language |
| Q04 | 49.5 | 8.535 | 3 | 34 | direct_answer_anchor_language |
| Q11 | 45.6 | 8.416 | 3 | 34 | direct_answer_anchor_language |
| Q13 | 42.76 | 8.901 | 3 | 36 | direct_answer_anchor_language |
| Q22 | 37.58 | 5.886 | 2 | 24 | direct_answer_anchor_language |
| Q26 | 35.0 | 5.904 | 2 | 24 | direct_answer_anchor_language |
| Q23 | 34.37 | 5.876 | 2 | 24 | direct_answer_anchor_language |
| Q15 | 31.24 | 5.821 | 2 | 24 | direct_answer_anchor_language |

Full table: [`data/v34_compute_profile_by_question.csv`](data/v34_compute_profile_by_question.csv).

## Role Runtime Distribution

| role_key | turns | wall_time | wall_share_pct | tokens_m | token_share_pct |
| --- | --- | --- | --- | --- | --- |
| agent | 184 | 3h 58m 54s | 34.37 | 44.207 | 33.84 |
| clerk | 220 | 5h 6m 6s | 44.04 | 54.239 | 41.52 |
| solver | 138 | 2h 30m 2s | 21.59 | 32.202 | 24.65 |

## Top Wall-Time Phases

| phase | turns | wall_time | wall_share_pct |
| --- | --- | --- | --- |
| artemis_exchange_2 | 46 | 1h 22m 22s | 11.85 |
| artemis_exchange_3 | 46 | 1h 10m 42s | 10.17 |
| aria_exchange_1 | 46 | 1h 10m 5s | 10.08 |
| aria_exchange_2 | 46 | 1h 8m 45s | 9.89 |
| artemis_exchange_1 | 46 | 1h 5m 54s | 9.48 |
| athena_synthesis | 46 | 1h 4m 47s | 9.32 |
| aria_exchange_3 | 46 | 1h 2m 58s | 9.06 |
| athena_open | 46 | 51m 33s | 7.42 |
| artemis_forced_solve | 36 | 48m 14s | 6.94 |
| artemis_report | 46 | 38m 53s | 5.6 |

## Where The Architecture Stands

The architecture is healthier than the contaminated score first suggested, but the claim is narrower. The strongest durable result is that Runtime-at-Boot memory is operationally real: it loads, survives reset, and is consulted by the roles. The next scientific question is whether a clean, answer-free boot layer can improve route discipline without leaking final objects.

## V35 Requirements From This Addendum

- Build an answer-free boot corpus before any long run.
- Scan studied text against exact answer keys and answer-key language before CB8 starts.
- Reject problem-index-specific hints for target benchmark items unless the benchmark is explicitly a replay diagnostic.
- Keep the synthetic boot acknowledgement and after-certification baseline restore path.
- Run a small dry-run slice before another 12-hour full-dataset pass.
- Freeze external API export unless an agent has explicit user approval and a sanitized payload.

## Tables Produced

- [`data/v34_answer_anchor_scan.csv`](data/v34_answer_anchor_scan.csv)
- [`data/v34_compute_profile_by_question.csv`](data/v34_compute_profile_by_question.csv)
- [`data/v34_forensic_summary.json`](data/v34_forensic_summary.json)

Generator: [`scripts/build_v34_forensic_addendum.py`](scripts/build_v34_forensic_addendum.py).
