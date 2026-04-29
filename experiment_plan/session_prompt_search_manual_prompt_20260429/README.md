# Session Prompt Search: Manual Prompt Artifact

Generated: 2026-04-29

Source artifact, local only:

`N:\Research\colab_outputs\aime_2026_prompt_manual_prompt_001_20260429-053802`

This folder records a derived analysis of the manual-prompt transcript. The raw transcript is intentionally not copied into the public repo because it contains private autobiographical material. The useful public artifact is the diagnosis: the trio became linguistically coherent, identified the correct meta-issue, and still failed the controller/task contract by forcing a benchmark-style integer closeout.

## Case Studied

**Too early agreement vs. full disagreement.**

The run was not a normal AIME integer problem. It was a human query asking the agents to formalize how they should be written as prompts, how they should disagree, and how their boot data should be understood.

The agents converged on the right conceptual hinge:

- forced disagreement creates phantom faults;
- blind agreement creates consensus hallucination;
- the right mechanism is adaptive friction with a truth anchor.

But the controller still forced a math-style final answer:

- `peer_validation_status`: `disagreement_open`
- `open_objections`: peer reports not distinct enough; Athena did not have an exact integer candidate
- Aria candidate: `none`, confidence `0`
- Artemis candidate: `none`, confidence `0`
- Athena synthesis candidate: `none`, confidence `0`
- Athena finalization: `\boxed{0}_confidence:0`
- run status: `closed_out_simple_answer_arbitration`
- verified: `true`

That is the exact failure: the language layer understood the problem better than the closeout layer.

## Main Conclusion

The session prompt should not say "disagree with peers." That produces performative opposition and phantom faults.

The session prompt should say:

1. math has one correct final answer;
2. agreement is valid only after independent route closure;
3. disagreement is valid only when anchored to a specific claim, invariant, boundary condition, arithmetic step, or problem-text constraint;
4. if no truth anchor exists, dismiss the objection as a phantom fault;
5. if the task is not asking for an integer, do not force a boxed integer.

## Folder Map

- [`session_prompt_candidate.md`](session_prompt_candidate.md): the proposed shared session prompt.
- [`system_prompt_implications.md`](system_prompt_implications.md): what this implies for system/session prompt design.
- [`data/manual_prompt_run_diagnostics.json`](data/manual_prompt_run_diagnostics.json): parsed controller and token/timing diagnostics.
- [`data/turn_summary_redacted.csv`](data/turn_summary_redacted.csv): redacted turn-level summary.

## Why This Matters For The Next Run

This artifact bridges the two failure families:

- AIME math failures: agents agree too early or finalize despite open blockers.
- Meta prompt failure: agents reason coherently about the correct disagreement mechanism but the controller coerces an invalid integer answer.

The next controller/session layer should preserve the good insight from the transcript: **Adaptive Friction, not constant disagreement.**
