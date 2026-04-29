# AEN V34 Next Run Package

Prepared on 2026-04-29 for the next full AIME-2026 dataset-route run.

## Ready Artifacts

| Artifact | Path |
|---|---|
| Next-run notebook | [`notebooks/AENAIMO260_0_2_3_V34_NEXT_RUN.ipynb`](../notebooks/AENAIMO260_0_2_3_V34_NEXT_RUN.ipynb) |
| Exact codeblocks embedded in notebook | [`next_run_v34/codeblocks/`](codeblocks/) |
| Runtime-at-Boot v34 dataset | [`runtimeatbootdataset_v34/`](../runtimeatbootdataset_v34/) |
| V34 dataset manifest | [`runtimeatbootdataset_v34/runtimeatboot_v34_manifest.json`](../runtimeatbootdataset_v34/runtimeatboot_v34_manifest.json) |

## Run Contract

- Prompt route is disabled by default in CB12.
- Dataset route is enabled by default in CB12.
- Dataset source remains `MathArena/aime_2026`.
- Runtime-at-Boot root defaults to `/kaggle/input/runtimeatbootdataset-v34`.
- `BOOT_MEMORY_STUDY_LINE_LIMIT=150`, so the 13 prepended V34 repair rows plus V31/V33 rows are studied.
- `GLOBAL_MAX_BIG_LOOPS=3`.
- `GLOBAL_MIN_BIG_LOOP_FOR_CLOSEOUT=1`.
- `GLOBAL_CLOSEOUT_CONFIDENCE_PCT=85`.
- Athena, Aria, and Artemis max turn budgets are restored to 50k, with 10k open/exchange/report budgets and 256 final tokens.

## Implemented Fixes

### 1. Strict Closeout Until Max Loop

The loop knob was not respected because the old CB7.5 closeout branch ended the run whenever `loop_no >= MIN_BIG_LOOP_FOR_CLOSEOUT` and any selected candidate existed. The V34 code now requires strict trio alignment before early closeout.

Relevant line references in [`codeblocks/cb07_5.py`](codeblocks/cb07_5.py):

```text
22   CB07_5_DYNAMIC_REVISION = "2026-04-29-cb075-strict-confidence-loop-closeout-v1.5.2"
24   MAX_BIG_LOOPS_DEFAULT = 3
2636 closeout_requires_exact_integer_consensus = True
2637 closeout_decision_rule = strict_trio_confidence_until_max_loop_then_best_confidence
3041 strict_closeout_ready = bool(...)
3051 max_loop_best_confidence_ready = bool(...)
3055 if strict_closeout_ready or max_loop_best_confidence_ready:
3070 controller_closeout_rule = strict_trio_confidence_until_max_loop_then_best_confidence
```

Pseudocode:

```python
strict_closeout_ready = (
    loop_no >= MIN_BIG_LOOP_FOR_CLOSEOUT
    and selected_candidate != "none"
    and final_trio_exact_alignment
    and final_confident_enough
    and peers_confident_enough
    and peer_reports_distinct
    and peer_validation_status == "confidence_aligned"
    and not closeout_objections
)

max_loop_best_confidence_ready = (
    loop_no >= MAX_BIG_LOOPS
    and selected_candidate != "none"
)

if strict_closeout_ready:
    verified = True
    status = "closed_out_strict_trio_confidence"
elif max_loop_best_confidence_ready:
    verified = True
    status = "closed_out_max_loop_best_confidence_arbitration"
else:
    continue
```

This makes loop 1 closeout possible for clean unanimous high-confidence cases like Q1, but forces another loop for cases like Q17 where the answer or confidence/peer validation is unresolved.

### 2. Adaptive-Friction Session Prompts

CB05 now gives all three roles the shared rule: the goal is the correct answer, not agreement. Every challenge needs a Truth Anchor; unsupported disagreement is a phantom fault; unsupported agreement is consensus risk.

Relevant line references in [`codeblocks/cb05.py`](codeblocks/cb05.py):

```text
16   CB05_PROMPTING_REVISION = 2026-04-29-cb05-v1.4.4-adaptive-friction-session-prompts
33   DEFAULT_ATHENA_SESSION_PROMPT
43   DEFAULT_ARTEMIS_SESSION_PROMPT
53   DEFAULT_ARIA_SESSION_PROMPT
```

### 3. V34 Runtime-at-Boot Dataset

V34 is additive on top of the existing Runtime-at-Boot package. It prepends 13 long answer-aware repair records for each role, one per full-run miss. Every added row is at least 22k characters, exceeding the requested 10k minimum.

This is intentionally an answer-aware internal repair ablation. It is not a blind public benchmark setting.

## Verified Miss Set

The answer key was verified against [MathArena/aime_2026](https://huggingface.co/datasets/MathArena/aime_2026), whose dataset card exposes `problem_idx`, `problem`, and `answer`, and says the AIME-2026 questions were extracted, converted to LaTeX, and verified.

| Problem | Verified answer | Prior full-run answer | Repair theme |
|---:|---:|---:|---|
| 7 | 396 | 341 | permutation cycle lengths divide 6 |
| 9 | 29 | 4133 | conditional probability over die orientation histories |
| 10 | 156 | 133 | coordinate rotation about circumcenter |
| 11 | 896 | 584 | grid cut extremal absolute differences |
| 15 | 83 | 1 | rectangular cell-loop tiling enumeration |
| 17 | 243 | 69 | directed trail transfer state across 10 squares |
| 18 | 503 | 505 | nonconvex polygon constraints and modular area |
| 21 | 50 | 18 | parabola normal/tangent radius sum |
| 23 | 245 | 125 | incenter perimeter ratio Diophantine search |
| 24 | 669 | 558 | repunit series floor and carry control |
| 28 | 107 | 12 | cousin-set component product optimization |
| 29 | 157 | 5 | left-associative parity-operation dynamic program |
| 30 | 393 | 364 | ordered ternary tuple count modulo 3 |

## Expected Next Step

Import [`AENAIMO260_0_2_3_V34_NEXT_RUN.ipynb`](../notebooks/AENAIMO260_0_2_3_V34_NEXT_RUN.ipynb), attach/upload the V34 Runtime-at-Boot dataset under the Kaggle slug `runtimeatbootdataset-v34`, run all cells, then analyze the new transcripts.
