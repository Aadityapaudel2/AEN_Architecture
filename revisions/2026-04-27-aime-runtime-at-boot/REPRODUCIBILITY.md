# Reproducibility: April 27 AIME RuntimeAtBoot Revision

This page is written for a reader who has not seen the private notebook history. It separates three things that are easy to mix together:

1. the frozen paper canon,
2. the April 27 result archive and analysis,
3. the corrected RuntimeAtBoot memory-preservation path.

## Public Inputs

| input | access path |
| --- | --- |
| Paper source and frozen reference tables | repository root `paper/` |
| AIME public benchmark data | Hugging Face dataset `MathArena/aime_2026` |
| April 27 Q1-Q30 analysis tables | `data/tables/` |
| April 27 visuals | `assets/q1_q30/` |
| RuntimeAtBoot v32 staged payload | `runtime_at_boot/runtimeatbootdataset/` |
| Critical notebook cells | `code/` |

## Offline Folder Layout

Place the repository checkout anywhere, then keep these relative paths intact:

```text
AEN_Architecture/
  paper/
  revisions/2026-04-27-aime-runtime-at-boot/
    assets/
    code/
    data/
    runtime_at_boot/
```

For a completely offline run, pre-download the Hugging Face parquet used by CB12 and set `BENCHMARK_HF_PARQUET_PATH` to the local file path instead of the `hf://` URL. The analysis tables and diagrams in this folder do not require network access.

## Execution Order

Run the notebook cells in this order after model/runtime configuration cells are present:

| order | cell/block | purpose |
| ---: | --- | --- |
| 1 | CB4 | role flags, runtime profile, paths, model choices |
| 2 | CB6 and CB6.5 | vLLM/OpenAI-compatible runtime helpers and sampling policy |
| 3 | CB7 and CB7.5 | controller, role prompts, runtime support helpers |
| 4 | `code/cb08_runtimeatboot_bootcert_v1_4_9.py` | load roles, study RuntimeAtBoot rows, certify, capture boot-memory baseline |
| 5 | `code/cb11_5_architecture_certificate_r4.py` | install boundary-reset wrapper that preserves the CB8 baseline |
| 6 | `code/cb12_aime2026_public_hf_runner.md` | load `MathArena/aime_2026` and run/export the benchmark rows |

CB12 does not need a code change for this revision. The correctness-critical change is the CB8/CB11.5 pair: CB8 must capture a baseline after studying boot memory, and CB11.5 r4 must restore that baseline after both the outer before/after-problem reset and the controller question reset.

## Success Signals

In CB8 output, expect RuntimeAtBoot certification to pass and report studied memory. In CB11.5 r4 reset and controller-reset restore events, look for:

```text
boot_memory_required: True
boot_memory_preserved: True
boot_memory_baseline_present: True
boot_memory_restored: True
cb11_5_controller_reset_boot_memory_restore
controller_question_reset_wrapper_installed: True
```

If `boot_memory_required` is true but any role lacks a baseline, the run should stop. That is intentional. A run that certifies boot memory and then wipes it before solving is not a valid RuntimeAtBoot transfer test.

## Rebuilding The April 27 Analysis Tables

The small CSVs under `data/tables/` are the public analysis layer. They summarize:

- frozen paper run: 15/30,
- paper unrestricted run: 22/30,
- current April 27 run: 21/30,
- slice-level accuracy,
- Q26-Q30 late-game outcomes,
- failure/warning taxonomy.

The raw private Colab transcript archives are not required to read the result layer in this GitHub package. They are retained locally for deeper audit, while the tables here provide the minimal public bridge from evidence to figures.

## Negative-Control Warning

One April 27 live path exposed an architecture bug: RuntimeAtBoot could pass certification, then a later question-boundary reset could erase the studied boot context before CB12 solving. The r4 wrapper is designed to catch exactly that state and to restore after the controller question reset itself. Treat any run without preserved baselines as an invalid memory-transfer run, even if MCQ certification passed.

## Public Path Caveats

Some manifest fields intentionally preserve local absolute paths such as `N:\`, `D:\`, or `C:\` as provenance. Public reproduction should use the repo-relative paths listed in this page. Treat the absolute paths as audit metadata, not required mount points.

The staged V32 answer-position distribution `A=4, B=4, C=5, D=5` refers to the first six strengthened certification rows per role, across 18 rows total. Legacy certification rows may use `probe_answer` instead of top-level `answer`; in particular, the Aria legacy cert file has top-level `answer` only on a small subset while `probe_answer` is populated throughout.
