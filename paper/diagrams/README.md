# Paper Diagrams

This folder contains the paper-native TikZ diagram sources used by `main.tex`.

- `aen_architecture.tex` - AEN overview that combines Runtime-at-Boot memory/certification with the solve-time role protocol.
- `aen_three_body_protocol.png` - Three-body protocol schema showing boot datasets, certification, Athena/Aria/Artemis, long-context substrate, and controller-owned final emission.
- `aen_n_body_local_protocol.png` - Proposed hierarchical local swarm extension where each node runs the AEN three-body protocol.
- `triadic_turn_protocol.tex` - Budgeted triadic controller-loop protocol and controller-owned finalization.
- `cb7_instruction_dispatch.tex` - CB7 prompt construction and explicit Athena/Aria/Artemis instruction dispatch.
- `single_model_vs_triad.tex` - Side-by-side distinction between repeated single-model sampling/voting and a controller-mediated Athena/Aria/Artemis triad.
- `controller_finalization_contract.tex` - Finalization-contract figure showing the Athena boxed-confidence block, controller parser, emission, and audit artifact.
- `*.pdf` - rendered vector diagrams.
- `*.png` - rendered bitmap diagrams for quick viewing.
- `render_diagrams.ps1` - regenerates the PDF and PNG versions from the TikZ sources.

These are generated diagram sources for the paper. The older copied PNG/SVG flowchart assets are not used in this draft.
