# System Prompt Implications

This is not the final system prompt. It is the implication set extracted from the manual-prompt run.

## What The Transcript Proved

The agents can now write coherent language and maintain role identity. That is a major milestone, but it is not mathematical competence by itself.

The failure was sharper:

- Aria and Artemis identified an excellent principle: distinguish real faults from phantom faults.
- Athena correctly noted that no concrete mathematical integer existed for the meta prompt.
- The controller still forced `\boxed{0}_confidence:0` and marked it verified.

Therefore, the next prompt layer must control both:

1. **agreement mechanics**: prevent blind consensus;
2. **task-type mechanics**: prevent integer closeout when the prompt asks for a design artifact.

## Prompt-Level Principle

Use the phrase **Truth Anchor**.

A Truth Anchor is the reason a challenge is real:

- exact problem text;
- invariant;
- theorem;
- arithmetic line;
- boundary case;
- case partition;
- boot-record discipline;
- contradiction with a stated constraint.

Without a Truth Anchor, a challenge is a phantom fault.

## Proposed System-Prompt Direction

```text
You are a closed-book mathematical verification system with three named roles. The goal is not harmony and not disagreement; the goal is route-closed truth.

Do not force benchmark integer output unless the user task asks for a benchmark integer. First classify the task type: math problem, prompt-design task, analysis task, dataset task, or controller-debug task. The final response must match the task type.

For math problems, close only after exact candidate agreement, independent route support, confidence above gate, and no unresolved blockers.

For prompt-design or analysis tasks, output the requested artifact directly. Do not fabricate a candidate integer. If a controller schema asks for candidate_answer_integer, use none with confidence 0.

Challenges must be anchored. A role may object only by citing the exact claim being challenged and the Truth Anchor that makes the challenge real. Disagreement without a Truth Anchor is a phantom fault and should be dismissed.

Agreement must also be anchored. A role may support closeout only by naming the route step it independently verified.
```

## Controller Implication

The session prompt can reduce errors, but it cannot fully fix the current closeout bug by itself. The controller must also reject closeout when:

- `peer_validation_status != confidence_aligned`;
- any role reports `candidate_answer_integer: none`;
- confidence is zero;
- the task type is non-integer;
- unresolved blockers remain.

The manual prompt artifact is the clean proof: the agents explicitly said the answer was `none`, then finalization converted it to `0`.

## Dataset Implication

Add answer-blind records teaching:

- adaptive friction;
- truth anchors;
- phantom-fault dismissal;
- task-type classification;
- "none is valid when no integer is asked";
- "do not turn conceptual closure into numerical closure."

These records should be short and repeated across Athena, Aria, and Artemis with role-specific responsibilities.
