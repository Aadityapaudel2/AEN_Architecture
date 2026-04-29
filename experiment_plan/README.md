# Experiment Plan: V31 Runtime-at-Boot to V34 Additive Repair

Generated: 2026-04-29T06:46:52Z

This folder prepares the next big run. It is centered on performance-enhancing ideas, not a retroactive paper claim.

## Open The UI

Start with [`index.html`](index.html). It gives the compact dashboard, the failure table, and links to the code and dataset proposals.

## Main Verdict

- V31/V33 Runtime-at-Boot should be preserved as the canonical base.
- V34 should be additive: small answer-blind route-study records aimed at stable miss axes.
- The concrete controller issue is closeout, not boot-read failure. CB8 has certified that the roles read the boot data.
- `GLOBAL_MAX_BIG_LOOPS = 3` is only a cap. Current CB7.5 closes at loop 1 whenever Athena finalization produces a selected candidate and `MIN_BIG_LOOP_FOR_CLOSEOUT <= 1`.
- Before a giant V34 run, review [`code_proposals/controller_loop_closeout_proposal.md`](code_proposals/controller_loop_closeout_proposal.md).

## Recorded Full-Run Baseline

Full run: `AIME-2026_export_full_dataset_30q_20260428-022518`

Accuracy: 17/30 = 56.67%

Full-run misses: aime2025_09, aime2025_10, aime2025_15, aime2025_17, aime2025_29, aime2025_30, aime2025_07, aime2025_11, aime2025_18, aime2025_21, aime2025_23, aime2025_24, aime2025_28

Stable misses with no correct recorded AIME-2026 attempt: aime2025_09, aime2025_10, aime2025_15, aime2025_17, aime2025_29, aime2025_30

## Failure Table

| qid | expected | full_run_answer | attempts | correct_attempts | stable_miss | peer_validation_full_run | topic | failure_mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aime2025_09 | 29 | 4133 | 2 | 0 | True | disagreement_open | Conditional probability on die-face sticker survival | Aria/Artemis disagreed, denominator logic was unstable, but Athena finalized anyway. |
| aime2025_10 | 156 | 133 | 2 | 0 | True | disagreement_open | Rotated triangle and nonconvex hexagon area | Open geometric/arithmetic blocker became a confident final answer. |
| aime2025_15 | 83 | 1 | 2 | 0 | True | confidence_aligned | Partitioning a 10x10 grid into rectangular cell loops | False uniqueness proof for nested squares. |
| aime2025_17 | 243 | 69 | 5 | 0 | True | disagreement_open | Directed path count in a ladder/diagonal graph without edge reuse | Repeated false closeouts across every recorded AIME-2026 attempt. |
| aime2025_29 | 157 | 5 | 2 | 0 | True | peer_aligned_waiting_athena | Left-associative custom operation over compositions of 12 | Stable undercount by invariant-only reasoning. |
| aime2025_30 | 393 | 364 | 2 | 0 | True | disagreement_open | Ordered 7-tuples modulo 3 with cyclic cubic sum | Enumeration acknowledged incomplete, then Athena finalized. |
| aime2025_07 | 396 | 341 | 2 | 1 | False | confidence_aligned | Permutation cycle types / order divides 6 | Complete consensus on a count with a missing conjugacy-class case. |
| aime2025_11 | 896 | 584 | 3 | 2 | False | disagreement_open | Maximizing grid adjacent differences | Peer disagreement between two degree-sorting totals; Athena selected one. |
| aime2025_18 | 503 | 505 | 2 | 1 | False | disagreement_open | Nonconvex pentagon coordinates and modular area filter | Near miss by off-by-two count. |
| aime2025_21 | 50 | 18 | 3 | 1 | False | peer_aligned_waiting_athena | Circle tangent to parabola, sum of possible radii | Recoverable algebraic route failure. |
| aime2025_23 | 245 | 125 | 2 | 1 | False | disagreement_open | Isosceles triangle incenter and integer side constraints | Open trig/number-theory blocker finalized as a candidate. |
| aime2025_24 | 669 | 558 | 2 | 1 | False | confidence_aligned | Infinite decimal/geometric series floor modulo 1000 | Consensus on coefficient extraction with floor/carry error. |
| aime2025_28 | 107 | 12 | 2 | 1 | False | disagreement_open | Counting cousin sets for finite integer sets | Capacity lower bound mistaken for exact-achievability proof. |

## Folder Map

- [`index.html`](index.html): visual planning UI.
- [`session_prompt_search_manual_prompt_20260429/`](session_prompt_search_manual_prompt_20260429/README.md): manual-prompt transcript diagnosis and session prompt candidate.
- [`dataset_proposal_v34.md`](dataset_proposal_v34.md): answer-blind V34 additive boot-record proposal for Athena, Aria, and Artemis.
- [`code_proposals/controller_loop_closeout_proposal.md`](code_proposals/controller_loop_closeout_proposal.md): exact current CB7.5 line references and pseudocode patch.
- [`code_proposals/next_run_config.py`](code_proposals/next_run_config.py): next-run knob block plus proposed closeout-safety toggles.
- [`data/aime2026_all_recorded_attempts.csv`](data/aime2026_all_recorded_attempts.csv): all parsed AIME-2026 attempts found under `N:\Research\colab_outputs`.
- [`data/failure_diagnosis.csv`](data/failure_diagnosis.csv): concise diagnosis table.
- [`data/problem_attempt_summary.csv`](data/problem_attempt_summary.csv): per-problem attempt matrix.
- [`data/run_summary.csv`](data/run_summary.csv): per-run score/timing summary.
- [`data/experiment_plan_summary.json`](data/experiment_plan_summary.json): UI source summary.
- [`visualizations/`](visualizations/): SVG summary figures.
