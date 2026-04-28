# Artificial Evaluation Network

AEN studies whether multi-role model architectures can turn reusable reasoning structure into measurable benchmark behavior.

## Start Here

| section | link |
| --- | --- |
| Frozen paper source | [paper/](https://github.com/Aadityapaudel2/AEN_Architecture/tree/main/paper) |
| Rendered preprint | [AEN_RAB_source_snapshot.pdf](https://github.com/Aadityapaudel2/AEN_Architecture/blob/main/artifacts/AEN_RAB_source_snapshot.pdf) |
| Revision ledger | [dated AIME artifacts](https://github.com/Aadityapaudel2/AEN_Architecture/tree/main/revisions) |
| April 27 benchmarkgrade | [Artifact 03](https://github.com/Aadityapaudel2/AEN_Architecture/tree/main/revisions/2026-04-27-artifact-03-benchmarkgrade-v023) |
| April 28 RuntimeAtBoot experiment | [Artifact 04](https://github.com/Aadityapaudel2/AEN_Architecture/tree/main/revisions/2026-04-28-artifact-04-runtime-at-boot-v33-experiment) |

## Revision Snapshot

| frozen pruned | unrestricted reference | Apr27 benchmarkgrade | Apr28 RuntimeAtBoot experiment |
| ---: | ---: | ---: | ---: |
| 15/30 | 22/30 | 21/30 | 17/30 |

The revision ledger is a follow-on evidence layer: AIME Q1-Q30 tables, RuntimeAtBoot staged data, diagrams, and the April 28 negative experiment showing that boot certification did not by itself preserve final-answer quality.

## Boundary

The live April 28 run is treated as diagnostic evidence until r4 certificates show preserved boot baselines at the controller reset boundary. This is intentional: the repository should make the architecture easier to audit, not easier to overclaim.
