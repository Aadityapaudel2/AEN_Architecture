# Controller Closeout Patch

## Problem

`GLOBAL_MAX_BIG_LOOPS=3` was read by CB7.5, but the controller still stopped at loop 1 because the final closeout branch accepted any selected candidate after `GLOBAL_MIN_BIG_LOOP_FOR_CLOSEOUT`.

Old behavior:

```python
if loop_no >= MIN_BIG_LOOP_FOR_CLOSEOUT and selected_candidate != "none":
    status = "closed_out_simple_answer_arbitration"
    verified = True
    break
```

That branch ignored existing closeout objections, peer validation status, trio answer alignment, peer distinctness, and confidence gates.

## V34 Behavior

Early closeout now requires:

- selected candidate exists
- trio exact alignment
- Athena confidence above gate
- peer confidence above gate
- peer reports distinct
- peer validation status is `confidence_aligned`
- no closeout objections

If any of those fail, the controller continues until `GLOBAL_MAX_BIG_LOOPS`. At max loop, it uses the existing arbitration/best-confidence candidate and marks the telemetry path as `closed_out_max_loop_best_confidence_arbitration`.

## Line References

See [`codeblocks/cb07_5.py`](codeblocks/cb07_5.py):

```text
3041 strict_closeout_ready = bool(...)
3051 max_loop_best_confidence_ready = bool(...)
3055 if strict_closeout_ready or max_loop_best_confidence_ready:
3056     status = "closed_out_strict_trio_confidence" or "closed_out_max_loop_best_confidence_arbitration"
3070     controller_closeout_rule = "strict_trio_confidence_until_max_loop_then_best_confidence"
```

## Intended Effect

- Q1-style clean unanimous high-confidence cases can close in loop 1.
- Q17-style disagreement or low-confidence cases must loop again.
- If the model still fails to converge by loop 3, the run still produces the best-confidence answer and auditable fallback telemetry.
