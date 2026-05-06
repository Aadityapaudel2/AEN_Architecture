# Token Cost Study

This folder records a narrow, auditable token-cost calculation for the five full AIME-2026 AEN runs already published in the revision ledger. It is deliberately not named `research` to avoid colliding with repository-level naming.

## Scope

This is a post-release runtime/accounting lens over AEN. It does not claim that AEN changes the underlying model architecture, sparsifies a dense model, or turns a dense 9B model into a mixture-of-experts model. Dense, MoE, quantization, serving kernels, batching, and hardware all affect the denominator through delivered throughput. AEN sits after model training and release: it is an orchestration protocol that changes how inference is used and audited.

The metric here uses `total_tokens` from the existing AEN run tables, so it should be read as cost per million logged tokens, not as a pure completion-token benchmark. For V34, the raw artifact separates prompt and completion tokens, but the earlier five-run comparison table is standardized on total logged tokens; the derived table therefore keeps that same basis for apples-to-apples comparison.

## Equation

Let:

- `T = total_logged_tokens`
- `S = total_wall_seconds`
- `R = T / S`, logged tokens per second
- `C = dollars_per_GPU_hour`
- `G = billable GPU-equivalent workers`

Then:

```text
cost_per_million_logged_tokens = (G * C / (R * 3600)) * 1,000,000
```

Equivalently, this folder reports the normalized coefficient:

```text
coefficient = 1,000,000 / (R * 3600)
actual_cost_per_million = coefficient * G * C
```

The coefficient is the dollar cost per million logged tokens when `G = 1` and `C = $1/GPU-hour`.

## Five-Run Calculation

| run | claim class | score | total logged tokens | total wall seconds | logged tokens/sec | normalized coefficient |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Frozen | blind/pruned baseline | 15/30 | 21,333,011 | 5,489.4 | 3,886.2 | $0.0715/M |
| Unrestricted | high-budget reference | 22/30 | 33,763,517 | 11,411.7 | 2,958.7 | $0.0939/M |
| Apr27 benchmark | compact benchmarkgrade | 21/30 | 3,858,740 | 10,307.2 | 374.4 | $0.7420/M |
| Apr28 RAB v33 | Runtime-at-Boot negative diagnostic | 17/30 | 4,033,378 | 11,557.1 | 349.0 | $0.7959/M |
| V34 answer-aware | answer-aware context-recall replay | 29/30 | 130,647,799 | 42,850.9 | 3,048.9 | $0.0911/M |

## Immediate Reading

- V34 is the massive-token run: 130.6M logged tokens across Q1-Q30, with 29/30 accuracy, but it is answer-aware context-recall replay rather than a blind benchmark.
- The compact April 27 and April 28 runs use far fewer tokens, but their logged token throughput is much lower in this table, so normalized cost per million logged tokens is higher under the wall-clock equation.
- Frozen and unrestricted have higher logged token throughput than the compact runs; V34 is in the same throughput band despite its much larger token budget.
- The useful denominator is not model architecture alone. For AEN, it is the realized runtime pipeline: prompt/context traffic, role scheduling, closeout policy, batching/serving behavior, and wall-clock throughput.

## Files

- `data/five_run_cost_per_token.csv`: exact derived table used for the charts.
- `visualizations/logged_tokens_per_second.svg`: logged-token throughput by run.
- `visualizations/cost_per_million_logged_tokens_normalized.svg`: normalized cost coefficient by run.
- `visualizations/score_vs_cost_per_million.svg`: score versus normalized cost coefficient.

## Source

Derived from `revisions/data/five_full_run_summary_q1_q30.csv` in this repository. No new benchmark data is introduced here.
