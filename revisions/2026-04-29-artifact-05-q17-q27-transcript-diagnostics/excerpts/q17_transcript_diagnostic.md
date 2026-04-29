# Q17 Transcript Diagnostic

## Verdict

Q17 is not a success in the latest selected export. The latest run `AIME-2026_export_explicit_problem_indices_3q_20260429-032853` submitted `32` while the strict key in `AIME-2026_PRIVATE_FULL.csv` is `243`.

The important failure mode is not invalid formatting. It is a high-confidence, loop-1, internally verified closeout on the wrong integer.

## Latest Closeout Shape

- submitted answer: `32`
- expected answer: `243`
- internal verified flag: `True`
- status: `closed_out_simple_answer_arbitration`
- loops: `1`
- total tokens: `2,207,900`
- peer validation status: `answer_aligned_waiting_confidence`
- closeout mode: `athena_mandatory_final_answer_turn`
- Athena / Aria / Artemis candidates: `32` / `32` / `32`
- Athena / Aria / Artemis confidence: `99` / `98` / `99`

## April 29 Prior Selected Attempt

The previous April 29 selected run `AIME-2026_export_explicit_problem_indices_3q_20260429-021145` submitted `7` against the same expected answer `243`. The later run changed the wrong answer from `7` to `32`, but did not recover the correct recurrence endpoint.

## Four-Artifact Ledger Check

The durable four-artifact ledger shows Q17 as:

| artifact | submitted | expected | correct | closeout |
| --- | ---: | ---: | --- | --- |
| Frozen pruned | 10 | 243 | False | Highest confidence |
| Unrestricted | 243 | 243 | True | Majority vote |
| Apr27 current 0.2.3 | 198 | 243 | False | athena_mandatory_final_answer_turn |
| Apr28 official boot run | 69 | 243 | False | athena_mandatory_final_answer_turn |


This matters because the existing repository ledger does **not** show Artifact 01 / frozen pruned as the correct Q17 run. It shows the unrestricted reference run as the Q17 correct run. If a separate frozen Q17 transcript exists, it is not present in the local export folders scanned for this artifact.

## Mechanism Inference

Q17 appears to be an endpoint-recurrence failure: several runs produced different plausible integers (`198`, `69`, `7`, `32`) while still permitting loop-1 finalization. The most recent selected run is the sharpest warning case because all visible role candidates aligned on `32` with high confidence, yet the score key says `243`.
