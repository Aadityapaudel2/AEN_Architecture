# April 28 RuntimeAtBoot Regression Note

This note accompanies the Four-Artifact Report copied into `four_artifact_report_20260428/`.

## Headline

The April 28 RuntimeAtBoot run did not validate a positive RuntimeAtBoot transfer claim. It scored 17/30, below the Artifact 03 run at 21/30 and below the unrestricted paper reference at 22/30.

| run | score | mean total tokens |
| --- | ---: | ---: |
| Frozen pruned | 15/30 | 711,100 |
| Unrestricted | 22/30 | 1,125,451 |
| Artifact 03 Apr27 benchmarkgrade v0.2.3 | 21/30 | 128,625 |
| Artifact 04 Apr28 RuntimeAtBoot experiment | 17/30 | 134,446 |

This is a negative result, and it is valuable: the certification/study system as run on Apr 28 degraded benchmark performance rather than improving it.

## What Changed In The New Run

The Apr28 boot summary differs from the prior successful Q28 Artifact 03 run in ways that matter:

- Certification was 25 probes per role, not the earlier 75-line frozen-style certification.
- `memory_studied` was reported true, but every role had `ack_success_count: 0`.
- The boot layer committed large baseline prompt state before solving: Artemis 45,088 tokens, Aria 45,503 tokens, Athena 57,077 tokens.
- The Apr28 RuntimeAtBoot experiment used the RuntimeAtBoot Kaggle paths under `/kaggle/input/runtimeatboot/boot/...`, while the prior successful Q28 artifact was not proof that this later v33/v32 stage was the exact Kaggle input.
- Controller finalization still allowed Athena to box an answer even when peer validation was not clean.

The strongest gate-level correction is therefore simple: `memory_studied: true` must not pass when `ack_success_count: 0`, and `peer_validation_status: disagreement_open` must hard-block finalization.

## Q28 Diagnostic

Q28 is the clearest single-question test case.

| run | answer | correct | total tokens | seconds |
| --- | ---: | --- | ---: | ---: |
| Frozen pruned | 4040 | false | 719,067 | 209.931 |
| Unrestricted | 107 | true | 1,182,933 | 525.031 |
| Artifact 03 Apr27 benchmarkgrade v0.2.3 | 107 | true | 145,529 | 407.937 |
| Artifact 04 Apr28 RuntimeAtBoot experiment | 12 | false | 116,594 | 391.047 |

Prior successful behavior: Artemis corrected the problem to a chain/factorization model for `4040 = 2^3 * 5 * 101`, giving cost `1 + 1 + 1 + 4 + 100 = 107`. Aria accepted the correction, and Athena synthesized `107`.

Artifact 04 failed behavior: Athena and Artemis converged on the capacity argument `2^11 < 4040 <= 2^12`, giving `12`. Aria explicitly did not have a solved candidate and left an exact-count feasibility blocker open. The controller state recorded `peer_validation_status: disagreement_open`, yet finalization still accepted `12`.

## Token Forensics

The Artifact 04 Q28 run did not simply spend more useful solve tokens. It spent fewer total solve tokens than Artifact 03, and it shifted token mass away from the role that previously found the correction.

| role | Artifact 03 total | Artifact 04 Apr28 experiment total | delta |
| --- | ---: | ---: | ---: |
| Athena / solver | 20,880 | 32,662 | +11,782 |
| Aria / agent | 53,493 | 42,292 | -11,201 |
| Artemis / clerk | 71,156 | 41,640 | -29,516 |
| Total | 145,529 | 116,594 | -28,935 |

The harmful pattern is not high total solve-token count. The harmful pattern is unvalidated boot-study state plus reduced independent audit budget plus a non-hard finalization gate.

## Working Hypotheses

1. The 25-line certification path was weaker than the prior 75-line mechanics and did not reproduce the frozen inference behavior.
2. The memory study layer was allowed to pass even though acknowledgements failed, so the run could carry expensive but uncertified context.
3. The controller treated disagreement as advisory instead of fatal during closeout.
4. RuntimeAtBoot may be useful only if its study/certification state is compact, acknowledged, and preserved without suppressing role-local audit work.

## Next Experiments

Run one question at a time before any full benchmark rerun.

1. Q28 control: Apr27 mechanics, no new boot study, confirm answer `107` and peer clean state.
2. Q28 75-line certification: restore frozen-style 75-line certification mechanics, no failed memory-study pass-through.
3. Q28 ack-gated memory study: require `ack_success_count == ack_count`; otherwise fail boot before solving.
4. Q28 controller hard-block: force `disagreement_open` to return no final closeout even if Athena proposes an integer.
5. Only after Q28 passes with clean gates, run Q26-Q30; only after Q26-Q30 behaves, run Q1-Q30.

This revision should be pushed as a negative/diagnostic result, not as a successful RuntimeAtBoot score claim.
