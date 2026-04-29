# Q27 Transcript Diagnostic

## Verdict

Q27 is a real latest-run recovery in `AIME-2026_export_explicit_problem_indices_3q_20260429-032853`: submitted `223`, expected `223`, strict score correct.

## Latest Closeout Shape

- submitted answer: `223`
- expected answer: `223`
- internal verified flag: `True`
- status: `closed_out_simple_answer_arbitration`
- loops: `1`
- total tokens: `2,258,286`
- peer validation status: `disagreement_open`
- closeout mode: `athena_mandatory_final_answer_turn`
- transcript flags: `irrational-route blocker surfaced; circumcenter recalculation present; incenter recalculation present`

## Why This One Closed Correctly

The transcript contains a visible contradiction-driven repair. The route first produced an irrational distance, which conflicts with the problem asking for a rational `m/n`. Athena then recalculated the coordinate symmetry/circumcenter/incenter geometry and recovered `RS = 175/48`, so `m+n = 223`.

That is a different shape from Q17. Q27 used the peer/open-blocker pressure productively: the irrational-result blocker forced a geometry-center correction. Q17 instead allowed aligned confidence around the wrong recurrence endpoint.

## Four-Artifact Ledger Check

| artifact | submitted | expected | correct | closeout |
| --- | ---: | ---: | --- | --- |
| Frozen pruned | 97 | 223 | False | Strict consensus |
| Unrestricted | 223 | 223 | True | Strict consensus |
| Apr27 current 0.2.3 | 67 | 223 | False |  |
| Apr28 official boot run | 223 | 223 | True | athena_mandatory_final_answer_turn |


The prior misses were `97` in the frozen pruned run and `67` in the April 27 benchmarkgrade run. The unrestricted reference and the latest Runtime-at-Boot-style selected run both recover `223`.
