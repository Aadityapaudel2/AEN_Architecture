# Analysis: What April 27 Actually Shows

## Result Layer

The April 27 archived current run finished AIME Q1-Q30 at 21/30. That places it above the frozen paper canon at 15/30 and below the unrestricted paper reference at 22/30.

| run | score | accuracy | mean total tokens |
| --- | ---: | ---: | ---: |
| Paper frozen pruned | 15/30 | 50.00% | 711,100 |
| Paper unrestricted | 22/30 | 73.33% | 1,125,451 |
| Current Apr27 0.2.3 | 21/30 | 70.00% | 128,625 |

The striking part is not only the score. It is the compression: the current run used far fewer tokens than either paper reference. That is promising, but it is not self-certifying. The boot-memory bug found later means low token volume must be interpreted as an experimental variable, not immediate proof that the model had all intended boot context active during solve.

## Where The Current Run Improved

The current system recovered several cases that the frozen canon missed, especially through Q11-Q14 and Q16-Q25. The likely architectural contributors are:

- stronger Canon-route opening structure,
- role-local continuity inside each problem,
- clearer peer reporting contracts,
- explicit answer arbitration diagnostics,
- more compact, less meandering turn budgets.

This is the good version of the April 27 story: the system became more directed. It spent less context on diffuse exploration and more on routed validation.

## Where The Current Run Still Broke

The miss taxonomy is sharper than the headline score:

| class | failure pattern | examples |
| --- | --- | --- |
| C1 | counted witnesses instead of distinct image values | Q4 |
| C2 | lost conditional denominator discipline | Q9 |
| C3 | used local branch counts instead of endpoint/state recurrences | Q17, Q29 |
| C4 | closed geometry or answer-contract arithmetic too early | Q10, Q21, Q27 |
| C5 | accepted incomplete exact-cover/modular enumeration | Q15, Q30 |
| CONTROL | accepted answers with unresolved validation state | Q18, Q23-Q26, Q28 |

The shared theme is premature closure. The architecture often found a plausible route, but did not always demand the final ledger that would make the route safe to submit.

## What The Prior Turn Got Right

The prior successful behavior was not magic memory. It was disciplined role separation: Athena could route, Aria could explore, Artemis could audit, and the controller could exploit agreement when the peer state was genuinely clean. On many recovered problems the roles did enough independent work that the final answer was not just a single-model guess wearing three names.

The current prompt and controller changes also improved practical throughput. The system became less ceremonial and more operational: fewer broad declarations, more structured slots, more direct candidate accounting.

## What Went Wrong In The Bad Turn

The dangerous failure was architectural, not just mathematical. A boot certification pass can look clean while still failing to prove that the studied rows survive into live solving. In the observed bad path, the question-boundary reset left the active roles with tiny system prompts and empty history. That makes the solve run a normal closed-book run after a boot ceremony, not a RuntimeAtBoot transfer run.

That is why CB11.5 r4 matters: it converts memory preservation from an informal hope into a hard gate. If RuntimeAtBoot has passed, a missing boot-memory baseline is an error, not a warning.

## The Opposite Lesson

A stricter controller can also fail in the opposite direction. If every uncertain peer state blocks forever, the system can become safe but inert. The target is not maximal refusal. The target is earned closeout: a final integer should be allowed when the ledger is complete, the candidate source is explicit, and the validation state is clean.

The April 27 v32 design therefore does not just add more memory. It adds class-specific ledger requirements. The model should learn the small invariant that keeps the route honest: image versus witness, target versus condition, endpoint state, geometry closure, exact-cover completeness, and validation governance.

## Best-World Interpretation Of RuntimeAtBoot v32

RuntimeAtBoot v32 is a targeted study layer. It is not meant to memorize AIME answers. The rows are non-isomorphic class artifacts, and certification is a fast reading gate. A meaningful pass requires three conditions:

1. study rows are actually injected as live context,
2. certification cannot be explained by fixed answer-letter tracking,
3. solve transcripts show the relevant invariant or ledger being used.

If those conditions hold and transfer still fails, the conclusion is useful: either the class artifact is too weak, the controller still closes too early, or the model can recall the row without applying it. Each is a real research result.
## Why The Pasted Live Run Is Not The Final RuntimeAtBoot Proof

The April 28 live log is an important diagnostic. It shows competitive, improved low-token solving behavior, but its CB11.5 certificates also show zero active dialogue messages and near-empty active system prompt estimates at the first turn of each problem. That signature is incompatible with a successful live RuntimeAtBoot memory transfer after CB8 study.

The failure mode is architectural, not conceptual: CB11.5 r3 restored around the outer protocol boundary, while the controller performed another raw question reset afterward. CB11.5 r4 wraps that controller reset and restores `_cb8_boot_memory_baseline` immediately after it. A corrected rerun should therefore show preserved baselines in both the reset event and the pre-turn certificate before being claimed as RuntimeAtBoot transfer evidence.
