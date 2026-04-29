# Artificial Evaluation Network

**AEN treats mathematical reasoning as a runtime architecture.** Instead of asking one model for one long completion, it organizes inference into roles: a solver, a verifier, an agentic synthesizer, a controller, and an optional Runtime-at-Boot memory layer.

The paper's central question is direct: can reusable reasoning structure become measurable benchmark behavior?

![AEN architecture](https://raw.githubusercontent.com/Aadityapaudel2/AEN_Architecture/main/paper/diagrams/aen_architecture.png)

## The Short Version

AEN is not just a prompt template. It is an auditable inference protocol. The controller owns turn order, token budgets, closeout, and answer extraction. The roles argue, verify, and synthesize. The logs make it possible to see whether a change improved reasoning or merely made the transcript longer.

The most important result so far is the April 27 benchmarkgrade run: **21/30 on AIME Q1-Q30** at roughly **11.4% of the unrestricted mean token budget**. The unrestricted reference reached 22/30, but spent about 8.75x more tokens per problem.

## Results Snapshot

| artifact | run | score | accuracy | mean tokens/problem |
| --- | --- | ---: | ---: | ---: |
| 01 | frozen pruned baseline | 15/30 | 50.00% | 711,100 |
| 02 | unrestricted reference | 22/30 | 73.33% | 1,125,451 |
| 03 | April 27 benchmarkgrade v0.2.3 | 21/30 | 70.00% | 128,625 |
| 04 | April 28 Runtime-at-Boot v33 experiment | 17/30 | 56.67% | 134,446 |

![Four artifact scoreboard](https://raw.githubusercontent.com/Aadityapaudel2/AEN_Architecture/main/revisions/visualizations/four_run_scoreboard_q1_q30.svg)

![Token efficiency](https://raw.githubusercontent.com/Aadityapaudel2/AEN_Architecture/main/revisions/visualizations/token_efficiency_four_run.svg)

## Why It Matters

The extraordinary part is not that every variant wins. It does not. The extraordinary part is that AEN makes the difference observable. Artifact 03 shows a highly efficient near-ceiling run. Artifact 04 shows a Runtime-at-Boot intervention that passed structural certification but still regressed final-answer performance. That negative result is not hidden. It is part of the evidence.

That is the point of the architecture: make reasoning systems easier to audit, compare, and improve.

## Start Here

| section | link |
| --- | --- |
| Frozen paper source | [paper/](https://github.com/Aadityapaudel2/AEN_Architecture/tree/main/paper) |
| Rendered preprint | [AEN_RAB_source_snapshot.pdf](https://github.com/Aadityapaudel2/AEN_Architecture/blob/main/artifacts/AEN_RAB_source_snapshot.pdf) |
| Revision ledger | [dated AIME artifacts](https://github.com/Aadityapaudel2/AEN_Architecture/tree/main/revisions) |
| April 27 benchmarkgrade | [Artifact 03](https://github.com/Aadityapaudel2/AEN_Architecture/tree/main/revisions/2026-04-27-artifact-03-benchmarkgrade-v023) |
| April 28 Runtime-at-Boot experiment | [Artifact 04](https://github.com/Aadityapaudel2/AEN_Architecture/tree/main/revisions/2026-04-28-artifact-04-runtime-at-boot-v33-experiment) |

## Boundary

The frozen paper source is preserved as the Zenodo-aligned preprint package. Later AIME runs, Runtime-at-Boot diagnostics, CSV tables, and visualizations live in the revision ledger so the historical record stays clean and followable.

## Artifact 05: Q17/Q27 Diagnostics

The April 29 selected-slice transcript diagnostics are available at [`Artifact 05`](https://github.com/Aadityapaudel2/AEN_Architecture/tree/main/revisions/2026-04-29-artifact-05-q17-q27-transcript-diagnostics). The key result is narrow: Q27 was recovered as `223`, while Q17 remained an internally verified false-confidence miss (`32` vs `243`).
